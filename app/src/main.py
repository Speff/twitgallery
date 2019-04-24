from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class process_user(Resource):
    def post(self):
        return {
                "status": "processing",
                "user_id": request.form["user_id"]
                }, 202

api.add_resource(process_user, '/process_user')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
