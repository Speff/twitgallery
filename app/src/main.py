import psycopg2
from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

pg_connect_info = "dbname=twitgallery user=tg_user password=docker host=db"

class process_user(Resource):
    def post(self):
        res = check_user_status(request.form["user_id"])
        return {
                "status": "processing",
                "user_id": res
                }, 202

api.add_resource(process_user, '/process_user')

def check_user_status(screen_name):
    try:
        conn = psycopg2.connect(pg_connect_info)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return "false"
    finally:
        return "true"


if __name__ == '__main__':
    app.run(host='0.0.0.0')
