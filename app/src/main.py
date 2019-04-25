import os
from datetime import datetime
import twitter
import psycopg2
from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

twit_api = twitter.Api(consumer_key=os.environ['CONSUMER_KEY'],
                  consumer_secret=os.environ['CONSUMER_SECRET'],
                  access_token_key=os.environ['ACCESS_TOKEN'],
                  access_token_secret=os.environ['ACCESS_TOKEN_SECRET'],
                  sleep_on_rate_limit=True);

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

class get_user(Resource):
    def get(self):
        screen_name = request.form["user_id"]

        user_status_result = get_user(screen_name)
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
api.add_resource(get_user, '/get_results')

def validate_searched_user(screen_name=None):
    try:
        timeline = twit_api.GetFavorites(screen_name=screen_name, count=1)
    except: return False
    else: return True

def get_user(screen_name=None):
    try: pg_con = psycopg2.connect(pg_connect_info)
    except:
        return {"status": "failed"}
    else:
        pg_cur = pg_con.cursor()
        pg_cur.execute("""DELETE FROM user_status WHERE screen_name=%s;""", (screen_name,))



def search_user(screen_name=None):
    try: pg_con = psycopg2.connect(pg_connect_info)
    except:
        return False
    else:
        try:
            favorites = twit_api.GetFavorites(screen_name=screen_name, count=200)
        except:
            pg_cur = pg_con.cursor()
            pg_cur.execute("""DELETE FROM user_status WHERE screen_name=%s;""", (screen_name,))
            pg_con.commit()
            pg_con.close()
            return False
        else:
            pg_cur = pg_con.cursor()
            for favorite in favorites:
                create_time = datetime.strptime(favorite.created_at, '%a %b %d %H:%M:%S +0000 %Y')
                str_create_time = create_time.strftime("%m/%d/%Y, %H:%M:%S")
                pg_cur.execute("""INSERT INTO twitter_posts(created_at, post_id, text, name, screen_name, profile_image_url, possibly_sensitive, post_url) VALUES(%s, %s, %s, %s, %s, %s, %s, %s);""",(str_create_time, favorite.id_str, favorite.text, favorite.user.name, favorite.user.screen_name, favorite.user.profile_image_url, str(favorite.possibly_sensitive), "https://twitter.com/"+favorite.user.screen_name+"/status/"+favorite.id_str)) 
                pg_cur.execute("""INSERT INTO user_favorites(screen_name, post_id) VALUES(%s,%s)""", (screen_name, favorite.id_str))
                try:
                    for index, media in enumerate(favorite.media):
                        pg_cur.execute("""UPDATE twitter_posts SET media_url_"""+str(index)+"""=%s WHERE post_id=%s;""",(media.media_url,favorite.id_str)) 
                except:
                    pass
                else:
                    pg_con.commit()
            # TODO - Add timer before deleting user entry to prevent over-reloading
            # TODO - Handle duplicates
            # TODO - async this function
            pg_cur.execute("""DELETE FROM user_status WHERE screen_name=%s""", (screen_name,))
            pg_con.commit()

        pg_con.close()

    return True

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
            search_user(screen_name)
            return "success"
        else:
            pg_con.close()
            return "user already in db"


if __name__ == '__main__':
    try:
        pg_con = psycopg2.connect(pg_connect_info)
    except:
        print("db error")
    else:
        pg_cur = pg_con.cursor()
        pg_cur.execute("""DELETE FROM user_status;""")
        pg_con.commit()
        pg_cur.execute("""DELETE FROM twitter_posts;""")
        pg_con.commit()
        pg_con.close()
    print("Started")
    app.run(host='0.0.0.0')
