from flask import Flask, render_template
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)

class formData(Resource):
    def get(self, name, age):
        return {'name': name, 'age': age}
    
api.add_resource(formData, '/helloworld/<string:name>/<int:age>')



if __name__ == '__main__':
    app.run(debug=True)