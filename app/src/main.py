import psycopg2
from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

pg_connect_info = "dbname=twitgallery user=tg_user password=docker host=db"

class process_user(Resource):
    def post(self):
        screen_name = request.form["user_id"]

        user_status_result = check_user_status(screen_name)
        if user_status_result == False:
            user_status = "db connection error"
            status_code = 500
        elif user_status_result == True:
            user_status = "db connected"
            status_code = 202

        return {
                "status": user_status,
                "user_id": screen_name
                }, status_code

api.add_resource(process_user, '/process_user')

def check_user_status(screen_name):
    try:
        pg_con = psycopg2.connect(pg_connect_info)
    except:
        return False
    else:
        pg_con.close()
        return True


if __name__ == '__main__':
    app.run(host='0.0.0.0')
