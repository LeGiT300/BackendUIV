from flask import Flask
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)

class HelloWorld(Resource):
    def get(self):
        return {'message': 'Hello World'}, 200
        
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help='Name can not be blank')
        args = parser.parse_args()

        return {'message': f"User, {args['name']} created"}, 201
    
api.add_resource(HelloWorld, '/user')
if __name__ == '__main__':
    app.run(debug=True)