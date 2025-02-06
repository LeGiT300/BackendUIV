from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy as sql
from Database.flaskSQL import (User, Profile, Image, Document)
import json
from flask_bcrypt import Bcrypt
import secrets
from werkzeug.utils import secure_filename
import os

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
    mail = data.get('email')

    user = User.query.filter_by(username=username).first()
    email = User.query.filter_by(email=mail).first()

    if not user or email:
        return json({'error': 'Invalid credentials'}), 401

    
    access_token = create_access_token(identity=user.id)
    return json({'access_token': access_token}), 201
    
    
#ROUTE TO FETCH USER DETAILS FROM TOKEN

@app.route('/profile', methods=['GET'])
def profile():
    current_user = get_jwt_identity()
    user = User.query.get(current_user)


    return json({
        'username': user.username,
        'email': user.email,
        'phone': user.phone
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
    # with app.app_context():
    #     db.create_all()