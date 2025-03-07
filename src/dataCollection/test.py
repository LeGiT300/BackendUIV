from flask import Flask, request, jsonify
import sys
import os

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


extractor = ImageExtractor()

app = Flask(__name__)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
# secret_key = secrets.token_urlsafe(32)

load_dotenv()
KEY = os.getenv('JWT_TOKEN')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uiv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', KEY)


db.init_app(app)


with app.app_context():
    db.create_all()


# Function to save file to storage
def save_file_to_storage(file):
    upload_folder = 'uploads/'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    file_path = os.path.join(upload_folder, secure_filename(file.filename))
    file.save(file_path)
    return file_path



#ADDING API ENDPOINTS
## 1. POST /get-documents

@app.route('/get-documents', methods=['POST'])
def get_document():
    # documentType = request.form.get('documentType')
    documentBack = request.files.get('documentBack')
    documentFront = request.files.get('documentFront')


    if not all([documentBack, documentFront]):
        return jsonify({'error': 'Missing required fields or files'}), 400
    
    save_file_to_storage(documentBack)
    doc_front_path = save_file_to_storage(documentFront)

    extracted_data = extractor.process_and_extract(doc_front_path)
    name, dob = extractor.parse_ocr_data(extracted_data)

    # Convert extracted date to a date object if available
    try:
        dob_obj = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
    except Exception:
        dob_obj = None

    new_user = User(name=extracted_data.get('name'),
                    date_of_birth=extracted_data.get('date_of_birth'))
    db.session.add(new_user)
    db.session.flush()  # Flush to obtain new_user.user_id before commit

    new_image = Image(image_url=doc_front_path, user_id=new_user.user_id)
    db.session.add(new_image)

    new_document = Document(
        document_url = doc_front_path,
        document_name = secure_filename(documentFront.filename),
        document_type = documentType,
        extracted_text = extracted_data,
        user_id = new_user.user_id
    )
    db.session.add(new_document)

    new_profile = Profile(user_id=new_user.user_id, verification=True)
    db.session.add(new_profile)
    db.session.commit()

    response_data =  {
        'name': name,
        'date_of_birth': dob,
        'ocr_text': extracted_data,
        'userId': new_user.user_id
    }

    return jsonify(response_data), 200

    


#ROUTE TO LOGIN AND GENERATE AN ACCESS TOKEN WHEN USER FACE IS VERIFIED
@app.route('/generate_token', methods=['POST'])
def generate_token():
    data = request.get_json()
    user_id = data.get('userId')
    selfie = request.files.get('selfie')

    if not user_id:
        return jsonify({'error': 'userId is required'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not selfie:
        return jsonify({'error': 'Selfie image is required!'}), 400
    
    
    selfie_image_path = save_file_to_storage(selfie)    

    

    if not user.images or len(user.images) == 0:
        return jsonify({'error': 'No registered image found for verification'}), 400
    
    registered_image_path = user.images[0].image_url
    comparator = Image_compare()
    match = comparator.compare(selfie_image_path, registered_image_path)
    
    if not match:
        return jsonify({'error': 'Face does not match the registered ID image'}), 401
    
    
    access_token = create_access_token(identity=str(user.user_id), expires_delta=timedelta(hours=1))
    user.profile.token = access_token
    user.profile.token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()

    return jsonify({'access_token': access_token}), 200

    
    
    
#ROUTE TO FETCH USER DETAILS FROM TOKEN

@app.route('/verify-user', methods=['GET'])
@jwt_required()
def verify_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found!'}), 404
    
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile or profile.token != request.headers.get('Authorization').split()[1]:
        return jsonify({'error': 'The token is either invalid or expired'}), 401
    
    
    if profile.token_expiry < datetime.utcnow():
        return jsonify({'error': 'The token is expired'}), 401
    

    return jsonify({
        'username': user.username,
        'date_of_birth': user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None,
        'userId': user.user_id,
        'email': user.email,
        'phone': user.phone,
        'images': [img.image_url for img in user.images],
        'documents': [doc.document_url for doc in user.documents]
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
    # with app.app_context():
    #     db.create_all()