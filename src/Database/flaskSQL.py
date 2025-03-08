from flask import Flask
from flask_sqlalchemy import SQLAlchemy as sql


from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uiv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = sql(app)


#CREATING THE DATABASE

# class User(db.Model):
#     _tablename_ = 'user'
#     user_id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(15), unique=True, nullable=False)
#     email = db.Column(db.String(80), unique=True, nullable=False)
#     phone = db.Column(db.String, unique=True, nullable=False)
#     password = db.Column(db.String, nullable=False)

#     profile = db.relationship('Profile', backref='user', uselist=False)
#     images = db.relationship('Image', backref='user', lazy=True)
#     documents = db.relationship('Document', backref='user', lazy=True)


# class Profile(db.Model):
#     _tablename_ = 'profile'
#     profile_ID = db.Column(db.Integer, primary_key=True)
#     verification = db.Column(db.Boolean, default=False, nullable=False)
#     token = db.Column(db.String(255), nullable=True)
#     token_expiry = db.Column(db.DateTime, nullable=True)
#     user_id = db.Column(
#         db.Integer,
#         db.ForeignKey('user.user_id'),
#         nullable=False,
#         unique=True
#     )


# class Image(db.Model):
#     __tablename__ = 'image'
#     image_id = db.Column(db.Integer, primary_key=True)
#     image_url = db.Column(db.String, nullable=False)
#     upload_date = db.Column(db.DateTime, default=datetime.now)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))


# class Document(db.Model):
#     __tablename__ = 'document'
#     document_url = db.Column(db.String, nullable=False)
#     document_id = db.Column(db.Integer, primary_key=True)
#     document_name = db.Column(db.String(15), unique=True, nullable=False)
#     document_type = db.Column(db.String(15), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))



class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    # username = db.Column(db.String(15), unique=True, nullable=True)
    # email = db.Column(db.String(80), unique=True, nullable=True)
    # phone = db.Column(db.String, unique=True, nullable=True)
    # password = db.Column(db.String, nullable=True)
    # Additional fields for document extraction
    name = db.Column(db.String(100), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)

    profile = db.relationship('Profile', backref='user', uselist=False)
    images = db.relationship('Image', backref='user', lazy=True)
    documents = db.relationship('Document', backref='user', lazy=True)


class Profile(db.Model):
    __tablename__ = 'profile'
    profile_ID = db.Column(db.Integer, primary_key=True)
    verification = db.Column(db.Boolean, default=False, nullable=False)
    token = db.Column(db.String(255), nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, unique=True)
   


class Image(db.Model):
    __tablename__ = 'image'
    image_id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))


class Document(db.Model):
    __tablename__ = 'document'
    document_id = db.Column(db.Integer, primary_key=True)
    document_url = db.Column(db.String, nullable=False)
    document_name = db.Column(db.String(15), unique=True, nullable=False)
    document_type = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    extracted_text = db.Column(db.Text, nullable=True)