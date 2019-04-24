import os
import twitter
import psycopg2
from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

twit_api = twitter.Api(consumer_key=os.environ['CONSUMER_KEY'],
                  consumer_secret=os.environ['CONSUMER_SECRET'],
                  access_token_key=os.environ['ACCESS_TOKEN'],
                  access_token_secret=os.environ['ACCESS_TOKEN_SECRET']);

pg_connect_info = "dbname=twitgallery user=tg_user password=docker host=db"

class process_user(Resource):
    def post(self):
        screen_name = request.form["user_id"]

        user_status_result = check_user_status(screen_name)
        if user_status_result == "db_error":
            user_status = "db connection error"
            status_code = 503
        else:
            user_status = user_status_result
            status_code = 202

        return {
                "status": user_status,
                "user_id": screen_name
                }, status_code

api.add_resource(process_user, '/process_user')

def validate_searched_user(screen_name=None):
    try:
        timeline = twit_api.GetFavorites(screen_name=screen_name, count=1)
    except: return False
    else: return True

def check_user_status(screen_name):
    if validate_searched_user(screen_name) == False: return "user not found"
    try:
        pg_con = psycopg2.connect(pg_connect_info)
    except:
        return "db_error"
    else:
        pg_cur = pg_con.cursor()
        pg_cur.execute("""SELECT status FROM user_status WHERE screen_name=%s;""", (screen_name,))
        user_status = pg_cur.fetchone()

        if user_status == None:
            pg_cur.execute("""INSERT INTO user_status(screen_name, status) VALUES (%s, 'started')""", (screen_name,))
            pg_con.commit()
            pg_con.close()
            return "success"
        else:
            pg_con.close()
            return user_status[0]


if __name__ == '__main__':
    app.run(host='0.0.0.0')
