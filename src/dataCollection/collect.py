from flask import Flask, request, jsonify
import sys
import os
import traceback

from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Try importing required modules with error handling
try:
    from Database.flaskSQL import (User, Profile, Image, Document, db)
    from Extraction.imageCompare import Image_compare
    from Extraction.imageO import ImageExtractor
except ImportError as e:
    print(f"Import Error: {e}")
    traceback.print_exc()
    # For testing, you might want to create mock classes if imports fail
    # This is just for diagnostics

from dotenv import load_dotenv
import logging

# Configure logging to file for better debugging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting application")

# Try initializing the extractor with error handling
try:
    extractor = ImageExtractor()
    logger.info("ImageExtractor initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ImageExtractor: {e}")
    traceback.print_exc()

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Load environment variables
load_dotenv()
KEY = os.getenv('JWT_TOKEN')
logger.debug(f"JWT_TOKEN environment variable present: {KEY is not None}")

# Configure Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uiv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', KEY)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Initialize JWT with error handling
try:
    jwt = JWTManager(app)
    logger.info("JWTManager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize JWTManager: {e}")
    traceback.print_exc()

# Initialize database
try:
    db.init_app(app)
    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    traceback.print_exc()

# Debug middleware to log all requests
@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())
    logger.debug('Form: %s', request.form)
    logger.debug('Args: %s', request.args)
    logger.debug('Files: %s', list(request.files.keys()) if request.files else "No files")
    
    # Debug multipart forms specifically
    if request.content_type and 'multipart/form-data' in request.content_type:
        logger.debug('Processing multipart form data')
        for key in request.form:
            logger.debug(f'Form field: {key} = {request.form[key]}')
        for file_key in request.files:
            file = request.files[file_key]
            logger.debug(f'File field: {file_key}, filename={file.filename}, content_type={file.content_type}')

# Modified file-saving function with better error handling
def save_file_to_storage(file, path=None):
    try:
        # Use a default upload folder if none provided.
        upload_folder = path if path is not None else 'uploads/'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Get a secure filename and construct the path
        secure_name = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, secure_name)
        
        # Save the file and log the result
        file.save(file_path)
        logger.debug(f"File saved successfully to {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        traceback.print_exc()
        raise

def resolve_file_path(file_path):
    """Helper function to resolve file paths"""
    if not file_path:
        return None
    
    if os.path.exists(file_path):
        return file_path
        
    # Get the filename from the path
    filename = os.path.basename(file_path)
    
    # Try common locations including the specific upload folders
    possible_paths = [
        file_path,
        os.path.abspath(file_path),
        os.path.join(project_root, file_path),
        os.path.join('uploads', filename),
        os.path.join('uploads', 'front', filename),
        os.path.join('uploads', 'back', filename),
        os.path.join(project_root, 'uploads', filename),
        os.path.join(project_root, 'uploads', 'front', filename),
        os.path.join(project_root, 'uploads', 'back', filename)
    ]
    
    logger.debug(f"Searching for {filename} in possible paths:")
    for path in possible_paths:
        logger.debug(f"Trying path: {path}")
        if os.path.exists(path):
            logger.info(f"Found file at: {path}")
            return path
            
    logger.warning(f"Could not find file in any of the possible locations: {filename}")
    return None

# Diagnostic endpoint to test basic functionality
@app.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({'status': 'OK', 'message': 'API is running'}), 200

# Diagnostic endpoint for file upload only
@app.route('/test-upload', methods=['POST'])
def test_upload():
    try:
        logger.debug("Received test-upload request")
        
        if 'file' not in request.files:
            logger.debug("No file part in request")
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            logger.debug("No selected file")
            return jsonify({'error': 'No selected file'}), 400
            
        # Try to save the file
        file_path = save_file_to_storage(file, 'uploads/test/')
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'path': file_path
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test-upload: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Endpoint to process documents.
@app.route('/get-documents', methods=['POST'])
def get_document():
    try:
        logger.debug("Processing /get-documents request")
        
        # Retrieve the two files.
        documentBack = request.files.get('documentBack')
        documentFront = request.files.get('documentFront')

        if not documentBack or not documentFront:
            missing = []
            if not documentBack: missing.append('documentBack')
            if not documentFront: missing.append('documentFront')
            logger.debug(f"Missing files: {missing}")
            return jsonify({'error': f'Missing required files: {", ".join(missing)}'}), 400

        # Define separate folders for each file.
        path_back = 'uploads/back/'
        path_front = 'uploads/front/'

        # Save the files to their respective folders.
        doc_back_path = save_file_to_storage(documentBack, path=path_back)
        doc_front_path = save_file_to_storage(documentFront, path=path_front)

        # Process OCR on the front document.
        extracted_data = extractor.process_and_extract(doc_front_path)
        parsed_data = extractor.parse_ocr_data(extracted_data)
        name, dob = parsed_data

        try:
            dob_obj = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
        except Exception as e:
            logger.warning(f"Could not parse date of birth: {e}")
            dob_obj = None

        # Create the new user and flush to obtain the user_id.
        new_user = User(name=name, date_of_birth=dob_obj)
        db.session.add(new_user)
        db.session.flush()  # Get new_user.user_id before commit
        logger.debug(f"Created new user with ID: {new_user.user_id}")

        # Generate timestamp for unique document names
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Handle front document first since it needs OCR text
        front_filename = secure_filename(documentFront.filename)
        doc_type = front_filename.rsplit('.', 1)[-1] if '.' in front_filename else 'unknown'
        
        # Create unique document names with timestamp
        front_doc_name = f"front_{timestamp}_{front_filename}"
        back_doc_name = f"back_{timestamp}_{secure_filename(documentBack.filename)}"
        
        # Create an Image record if it's an image file
        if front_filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            new_image = Image(image_url=doc_front_path, user_id=new_user.user_id)
            db.session.add(new_image)
            logger.debug(f"Added front image for user {new_user.user_id}")
        
        # Create a Document record for the front document with OCR text
        front_document = Document(
            document_url=doc_front_path,
            document_name=front_doc_name,  # Using unique name with timestamp
            document_type=doc_type,
            extracted_text=extracted_data,
            user_id=new_user.user_id
        )
        db.session.add(front_document)
        logger.debug(f"Added front document for user {new_user.user_id}")

        # Process back document
        back_filename = secure_filename(documentBack.filename)
        if back_filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            new_image = Image(image_url=doc_back_path, user_id=new_user.user_id)
            db.session.add(new_image)
            logger.debug(f"Added back image for user {new_user.user_id}")
        else:
            back_document = Document(
                document_url=doc_back_path,
                document_name=back_doc_name,  # Using unique name with timestamp
                document_type=back_filename.rsplit('.', 1)[-1],
                user_id=new_user.user_id
            )
            db.session.add(back_document)
            logger.debug(f"Added back document for user {new_user.user_id}")

        new_profile = Profile(user_id=new_user.user_id, verification=True)
        db.session.add(new_profile)
        db.session.commit()
        logger.debug(f"Added profile and committed changes for user {new_user.user_id}")

        response_data = {
            'name': name,
            'date_of_birth': dob,
            'ocr_text': extracted_data,
            'userId': new_user.user_id
        }

        return jsonify(response_data), 200
    except Exception as e:
        logger.error(f"Error in get_document: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ROUTE TO LOGIN AND GENERATE AN ACCESS TOKEN WHEN USER FACE IS VERIFIED
UPLOAD_FOLDERS = {
    'selfies': 'uploads/selfies',
    'front': 'uploads/front',
    'back': 'uploads/back'
}

# Ensure upload directories exist
for folder in UPLOAD_FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

@app.route('/generate-token', methods=['POST'])
def generate_token():
    try:
        logger.info("========== GENERATE TOKEN REQUEST ==========")
        
        # Extract userId from form data
        user_id = request.form.get('userId')
        if not user_id:
            logger.error("Missing user ID")
            return jsonify({'error': 'Missing user ID'}), 400
        if not user_id.isdigit():
            logger.error("Invalid user ID format")
            return jsonify({'error': 'Invalid user ID'}), 400

        # Extract selfie image from request files
        if 'selfie' not in request.files:
            logger.error("Selfie image is required")
            return jsonify({'error': 'Selfie image is required'}), 400
        selfie = request.files['selfie']
        if not selfie.filename:
            logger.error("Selfie filename is empty")
            return jsonify({'error': 'Selfie file must have a filename'}), 400

        # Save the selfie image
        selfie_image_path = save_file_to_storage(selfie, path=UPLOAD_FOLDERS['selfies'])
        logger.info(f"Saved selfie image to: {selfie_image_path}")

        # Retrieve the user by user_id
        user = User.query.get(int(user_id))
        if not user:
            logger.error(f"User not found: {user_id}")
            return jsonify({'error': 'User not found'}), 404

        # Ensure the user has at least one registered image
        if not user.images or len(user.images) == 0:
            logger.error(f"No registered image found for user {user_id}")
            return jsonify({'error': 'No registered image found for verification'}), 400

        # Compare the selfie against registered images
        comparator = Image_compare()
        match_found = False
        attempted_paths = []

        for image in user.images:
            registered_image_path = image.image_url
            logger.info(f"Checking registered image: {registered_image_path}")
            
            # Try to resolve the correct path
            resolved_path = resolve_file_path(registered_image_path)
            if not resolved_path:
                logger.warning(f"Could not resolve path for: {registered_image_path}")
                attempted_paths.append({
                    'original': registered_image_path,
                    'attempted': [
                        os.path.join('uploads', 'front', os.path.basename(registered_image_path)),
                        os.path.join('uploads', 'back', os.path.basename(registered_image_path))
                    ]
                })
                continue

            logger.info(f"Found registered image at: {resolved_path}")
            
            try:
                if comparator.compare(selfie_image_path, resolved_path):
                    match_found = True
                    logger.info(f"Face match found with image: {resolved_path}")
                    break
            except Exception as e:
                logger.error(f"Error comparing images: {e}")
                attempted_paths.append({
                    'path': resolved_path,
                    'error': str(e)
                })
                continue

        if not match_found:
            logger.error("Face verification failed")
            return jsonify({
                'error': 'Face verification failed',
                'details': {
                    'attempted_paths': attempted_paths,
                    'selfie_path': selfie_image_path,
                    'search_locations': [
                        'uploads/front',
                        'uploads/back',
                        'uploads/selfies'
                    ]
                }
            }), 401

        # Generate JWT token (expires in 60 seconds)
        access_token = create_access_token(
            identity=str(user.user_id), 
            expires_delta=timedelta(seconds=60)
        )

        # Update or create user profile with token details
        if not user.profile:
            user.profile = Profile(user_id=user.user_id, verification=True)
        user.profile.token = access_token
        user.profile.token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        logger.info(f"Token generated successfully for user {user_id}")
        return jsonify({'access_token': access_token}), 200

    except Exception as e:
        logger.error(f"Error in generate_token endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


# ROUTE TO FETCH USER DETAILS FROM TOKEN
@app.route('/verify-user', methods=['GET'])
@jwt_required()
def verify_user():
    try:
        logger.info("Processing /verify-user request")
        
        user_id = get_jwt_identity()
        logger.info(f"JWT identity: {user_id}")
        
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return jsonify({'error': 'User not found!'}), 404

        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            logger.error(f"Profile not found for user: {user_id}")
            return jsonify({'error': 'User profile not found'}), 404
            
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error(f"Invalid authorization header: {auth_header}")
            return jsonify({'error': 'Invalid authorization header'}), 401
            
        token = auth_header.split(' ')[1]
        if profile.token != token:
            logger.error("Token mismatch")
            return jsonify({'error': 'The token is invalid'}), 401

        # Check if token is expired
        if profile.token_expiry and profile.token_expiry < datetime.utcnow():
            logger.error("Token expired")
            return jsonify({'error': 'The token is expired'}), 401

        # Only include fields that exist in the User model
        response = {
            'userId': user.user_id,
            'name': user.name,
            'date_of_birth': user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None,
            'verification_status': profile.verification if profile else False,
            'images': [img.image_url for img in user.images] if user.images else [],
            'documents': [
                {
                    'url': doc.document_url,
                    'type': doc.document_type,
                    'extracted_text': doc.extracted_text
                } for doc in user.documents
            ] if user.documents else []
        }
        
        logger.info(f"Returning user data for user {user_id}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error in verify_user: {e}")
        traceback.print_exc()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    logger.error(f"400 Bad Request: {error}")
    return jsonify({
        'error': 'Bad request',
        'message': str(error),
        'status_code': 400
    }), 400

@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 Not Found: {error}")
    return jsonify({
        'error': 'Not found',
        'message': str(error),
        'status_code': 404
    }), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"500 Server Error: {error}")
    traceback.print_exc()
    return jsonify({
        'error': 'Server error',
        'message': str(error),
        'status_code': 500
    }), 500

if __name__ == '__main__':
    logger.info("Starting Flask server")
    app.run(debug=True)