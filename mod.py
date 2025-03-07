from flask import Flask, request, jsonify, abort
import sys
import os
import uuid
import magic
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required, get_jwt_identity)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from Database.flaskSQL import (User, Profile, Image, Document, db)
from Extraction.imageCompare import Image_compare
from Extraction.imageO import ImageExtractor

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

extractor = ImageExtractor()

app = Flask(__name__)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Load environment variables
load_dotenv()
KEY = os.getenv('JWT_TOKEN')

# Validate required environment variables
if not os.getenv('JWT_SECRET_KEY'):
    logger.critical("JWT_SECRET_KEY environment variable not set")
    raise EnvironmentError("JWT_SECRET_KEY must be set in environment")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///uiv.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

# Define allowed file types and max file size
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

db.init_app(app)

with app.app_context():
    db.create_all()

# Function to check if file is allowed
def allowed_file(file):
    # Check file extension
    if not '.' in file.filename:
        return False
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    if file_size > MAX_FILE_SIZE:
        return False
    
    # Verify content type with python-magic
    mime = magic.Magic(mime=True)
    file_data = file.read(2048)  # Read a sample of the file
    file.seek(0)  # Reset file pointer
    mime_type = mime.from_buffer(file_data)
    
    allowed_mime_types = [
        'image/jpeg', 
        'image/png', 
        'application/pdf'
    ]
    
    return mime_type in allowed_mime_types

# Function to save file to storage with enhanced security
def save_file_to_storage(file):
    if not file or not allowed_file(file):
        logger.warning(f"Invalid file upload attempt: {file.filename if file else 'None'}")
        raise ValueError("Invalid file type or size")
    
    # Generate secure filename with UUID to prevent collisions and path traversal
    original_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    secure_filename = f"{uuid.uuid4().hex}.{original_extension}"
    
    # Create nested directory structure based on date to organize files
    upload_date = datetime.now().strftime('%Y/%m/%d')
    upload_folder = os.path.join('uploads', upload_date)
    
    # Create directory if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_folder, secure_filename)
    file.save(file_path)
    
    logger.info(f"File saved: {file_path}")
    return file_path


# ADDING API ENDPOINTS
## 1. POST /get-documents
@app.route('/get-documents', methods=['POST'])
@limiter.limit("10/hour")  # Limit to prevent abuse
def get_document():
    try:
        # Validate input fields
        documentType = request.form.get('documentType')
        if not documentType or not isinstance(documentType, str) or len(documentType) > 100:
            return jsonify({'error': 'Invalid document type'}), 400
        
        documentBack = request.files.get('documentBack')
        documentFront = request.files.get('documentFront')

        if not all([documentType, documentBack, documentFront]):
            return jsonify({'error': 'Missing required fields or files'}), 400
        
        try:
            # Save files with validations
            doc_back_path = save_file_to_storage(documentBack)
            doc_front_path = save_file_to_storage(documentFront)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Extract data with error handling
        try:
            extracted_data = extractor.process_and_extract(doc_front_path)
            name, dob = extractor.parse_ocr_data(extracted_data)
        except Exception as e:
            logger.error(f"Data extraction error: {str(e)}")
            return jsonify({'error': 'Failed to extract data from document'}), 422
        
        # Convert extracted date to a date object if available
        try:
            dob_obj = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
        except Exception as e:
            logger.warning(f"Date parsing error: {str(e)}")
            dob_obj = None

        # Create database records within a transaction
        try:
            new_user = User(name=extracted_data.get('name'),
                        date_of_birth=dob_obj)
            db.session.add(new_user)
            db.session.flush()  # Flush to obtain new_user.user_id before commit

            new_image = Image(
                image_url=doc_front_path, 
                user_id=new_user.user_id,
                upload_date=datetime.utcnow()
            )
            db.session.add(new_image)

            new_document = Document(
                document_url=doc_front_path,
                document_name=str(uuid.uuid4()),  # Don't use original filename
                document_type=documentType,
                extracted_text=extracted_data,
                user_id=new_user.user_id,
                upload_date=datetime.utcnow()
            )
            db.session.add(new_document)

            new_profile = Profile(user_id=new_user.user_id, verification=True)
            db.session.add(new_profile)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error: {str(e)}")
            return jsonify({'error': 'Failed to save data'}), 500

        response_data = {
            'name': name,
            'date_of_birth': dob,
            'userId': new_user.user_id
        }

        return jsonify(response_data), 200
    except Exception as e:
        logger.error(f"Unhandled exception in get_document: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


# ROUTE TO LOGIN AND GENERATE AN ACCESS TOKEN WHEN USER FACE IS VERIFIED
@app.route('/generate_token', methods=['POST'])
@limiter.limit("5/minute; 20/hour")  # More strict rate limiting for authentication
def generate_token():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        user_id = data.get('userId')
        if not user_id:
            return jsonify({'error': 'userId is required'}), 400
        
        # Use parameterized query through ORM
        user = User.query.get(user_id)
        if not user:
            # Use same error message to prevent user enumeration
            return jsonify({'error': 'Authentication failed'}), 401
        
        selfie = request.files.get('selfie')
        if not selfie:
            return jsonify({'error': 'Selfie image is required'}), 400
        
        try:
            selfie_image_path = save_file_to_storage(selfie)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not user.images or len(user.images) == 0:
            # Use same error message to prevent user enumeration
            return jsonify({'error': 'Authentication failed'}), 401
        
        registered_image_path = user.images[0].image_url
        
        try:
            comparator = Image_compare()
            match = comparator.compare(selfie_image_path, registered_image_path)
        except Exception as e:
            logger.error(f"Face comparison error: {str(e)}")
            return jsonify({'error': 'Face verification failed'}), 500
        
        if not match:
            # Log failed attempts for security monitoring
            logger.warning(f"Failed face verification attempt for user_id: {user_id}")
            return jsonify({'error': 'Authentication failed'}), 401
        
        # Create JWT token with appropriate expiration
        access_token = create_access_token(
            identity=str(user.user_id), 
            expires_delta=timedelta(hours=1)
        )
        
        # Update profile with token info
        user.profile.token = access_token
        user.profile.token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        return jsonify({'access_token': access_token}), 200
    except Exception as e:
        logger.error(f"Unhandled exception in generate_token: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    
    
# ROUTE TO FETCH USER DETAILS FROM TOKEN
@app.route('/verify-user', methods=['GET'])
@jwt_required()
@limiter.limit("30/minute")  # Rate limit to prevent abuse
def verify_user():
    try:
        user_id = get_jwt_identity()
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile or profile.token != request.headers.get('Authorization').split()[1]:
            return jsonify({'error': 'Invalid authentication'}), 401
        
        if profile.token_expiry < datetime.utcnow():
            return jsonify({'error': 'Authentication expired'}), 401
        
        # Return only necessary information
        return jsonify({
            'username': user.username,
            'date_of_birth': user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None,
            'userId': user.user_id,
            'email': user.email,
            'phone': user.phone,
            # Don't return full image paths, just IDs or sanitized references
            'images_count': len(user.images) if user.images else 0,
            'documents_count': len(user.documents) if user.documents else 0
        }), 200
    except Exception as e:
        logger.error(f"Unhandled exception in verify_user: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Do not use debug=True in production
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))