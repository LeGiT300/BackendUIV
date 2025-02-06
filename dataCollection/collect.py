from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy as sql
from Database.flaskSQL import User, Profile, Image, Document
import json
from flask_bcrypt import Bcrypt
import secrets
from werkzeug.utils import secure_filename
import os

from datetime import datetime, timedelta
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required, get_jwt_identity)


app = Flask(__name__)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
secret_key = secrets.token_urlsafe(32)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uiv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRETE_KEY'] = secret_key

db = sql(app)

# Function to save file to storage
def save_file_to_storage(file):
    upload_folder = 'uploads/'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    file_path = os.path.join(upload_folder, secure_filename(file.filename))
    file.save(file_path)
    return file_path

#ADDING API ENDPOINTS
#ADDING API ENDPOINTS


#ROUTE TO VALIDATE THE FORM AND REGISTER NEW USERS
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    mail = data.get('email')
    tel = data.get('phone')
    password = data.get('password')


    if not all([username, mail, tel, password]):
        return json({'error': 'Missing Username'}), 400 
    
    hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')
    if User.query.filter_by(username=username).first():
        return json({'error': 'Username already exists!'}), 400

    new_user = User(username=username, email=mail, phone=tel, password=hashed_pwd)
    db.session.add(new_user)
    db.session.commit()

    #document upload

    uploaded = request.files.getlist('files')
    for file in uploaded:
        if file.filename == '':
            continue

        filename = secure_filename(file.filename)
        file_url = save_file_to_storage(file)
        if filename.lower().endswith('jpg', 'png', 'jpeg'):
            new_image = Image(image_url=file_url, user_id=new_user.user_id)

        else:
            new_doc = Document(
                document_name=filename, 
                document_type=filename.split('.')[-1],
                document_url = file_url,
                user_id = new_user.user_id
            )

        db.session.add(new_doc)
    
    db.session.commit()
    return json({'message': 'User Created Successfully!'}), 200


#ROUTE TO LOGIN AND GENERATE AN ACCESS TOKEN
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    h_password = bcrypt.check_password_hash(user.password, password)

    if not user or h_password:
        return json({'error': 'Invalid credentials'}), 401
    
    
    access_token = create_access_token(identity=user.user_id, expires_delta=timedelta(seconds=60))

    user.profile.token = access_token
    user.profile.token_expiry = datetime.utcnow() + timedelta(seconds=60)
    db.session.commit()

    return json({'access_token': access_token}), 201
    
    
#ROUTE TO FETCH USER DETAILS FROM TOKEN

@app.route('/user', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return ({'error': 'User not found!'}), 404
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile or profile.token != request.headers.get('Authorization').split()[1]:
        return json({'error': 'The token is either invalid or expired'}), 401
    
    if profile.token_expiry < datetime.utcnow():
        return json({'error': 'The token is expired'}), 401
    

    return json({
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'images': [img.image_url for img in user.images],
        'documents': [doc.document_url for doc in user.documents]
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
    # with app.app_context():
    #     db.create_all()