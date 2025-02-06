from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy as sql
from flask_bcrypt import Bcrypt

from flask_jwt_extended import (JWTManager, create_access_token, jwt_required, get_jwt_identity)

from datetime import datetime
import secrets
import json

secret_key = secrets.token_urlsafe(32)
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uiv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRETE_KEY'] = secret_key

db = sql(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

#CREATING THE DATABASE

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.Integer, unique=True, nullable=False)
    profile_ID = db.Column(db.Integer, db.ForeignKey('profile.profile_ID'))




class Profile(db.Model):
    __tablename__ = 'profile'
    profile_ID = db.Column(db.Integer, primary_key=True)
    verification = db.Column(db.Boolean, nullable=False)
    token = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))



class Image(db.Model):
    __tablename__ = 'image'
    image_id = db.Column(db.Integer, primary_key=True)
    upload_date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))


class Document(db.Model):
    __tablename__ = 'document'
    document_id = db.Column(db.Integer, primary_key=True)
    document_name = db.Column(db.String(15), unique=True, nullable=False)
    document_type = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))


#ADDING API ENDPOINTS


#ROUTE TO VALIDATE THE FORM AND REGISTER NEW USERS
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    mail = data.get('email')
    tel = data.get('phone')


    if not username:
        return json({'error': 'Missing Username'}), 400 
    

    if User.query.filter_by(username=username).first():
        return json({'error': 'Username already exists!'}), 400

    new_user = User(username=username, email=mail, phone=tel)
    db.session.add(new_user)
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