#!/usr/bin/sh

import psycopg2
import config
from configparser import ConfigParser
from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class process_user(Resource):
    def get(self, user_id):
        ret = user_id + ' accepted'
        return {'status': ret}, 202 # Accepted user

api.add_resource(process_user, '/<string:user_id>')

if __name__ == '__main__':
    app.run()
