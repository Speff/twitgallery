import os
import sys
import signal
from datetime import datetime
import twitter
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, session
from flask_restful import Resource, Api
import oauth2 as oauth
import urllib.parse
import uuid


app = Flask(__name__)
api = Api(app)
app.secret_key = os.environ["IPSO_COOKIE_AUTH"].encode("utf-8")

twit_api = twitter.Api(consumer_key=os.environ['CONSUMER_KEY'],
                  consumer_secret=os.environ['CONSUMER_SECRET'],
                  access_token_key=os.environ['ACCESS_TOKEN'],
                  access_token_secret=os.environ['ACCESS_TOKEN_SECRET'])

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

class get_results(Resource):
    def post(self):
        screen_name = request.form["user_id"]
        offset = request.form["offset"]

        user_status_result = get_user(screen_name, offset)

        if user_status_result == "no more results":
            user_status = user_status_result
            status_code = 204
        elif user_status_result == "db_error":
            user_status = "db connection error"
            status_code = 503
        else:
            user_status = user_status_result
            status_code = 202

        return {
                "status": user_status,
                "user_id": screen_name
                }, status_code
class get_auth_url(Resource):
    def get(self):
        if request.method == "GET":
            ret_uuid = str(uuid.uuid4())

            session['tg_guid'] = ret_uuid

            consumer_key = os.environ['CONSUMER_KEY']
            consumer_secret = os.environ['CONSUMER_SECRET']
            consumer = oauth.Consumer(consumer_key, consumer_secret)

            request_token_url = 'https://api.twitter.com/oauth/request_token'
            authorize_url = 'https://api.twitter.com/oauth/authorize'

            client = oauth.Client(consumer)

            resp, content = client.request(request_token_url, "GET")
            if resp['status'] != '200':
                return {"status": "Twitter unavailable"}, 500
            
            request_token = dict(urllib.parse.parse_qsl(content))
            oauth_token_secret = request_token["oauth_token_secret".encode("utf-8")].decode("utf-8")

            try:
                pg_con = psycopg2.connect(pg_connect_info)
                pg_cur = pg_con.cursor()
                pg_cur.execute("""INSERT INTO user_keys(session_current_user, oauth_token_secret) VALUES (%s, %s)""", (ret_uuid, oauth_token_secret))
                pg_con.commit()
                pg_con.close()
            except psycopg2.Error as e:
                print(e)
                return {"status": "db insert failed"}, 500

            return {
                    "auth_url": "%s?oauth_token=%s" % (authorize_url, str(request_token["oauth_token".encode("utf-8")].decode("utf-8")))
                    }, 201

class auth_twit(Resource):
    def get(self):
        if "tg_guid" in session:
            if request.method == 'GET':
                oauth_token = request.args.get("oauth_token")
                try:
                    pg_con = psycopg2.connect(pg_connect_info)
                    pg_cur = pg_con.cursor()
                    pg_cur.execute("""SELECT oauth_token_secret FROM user_keys WHERE session_current_user=%s""", (session["tg_guid"],))
                    oauth_token_secret = pg_cur.fetchone()[0]
                    pg_con.close()
                except psycopg2.Error as e:
                    print(e)
                    return {"status": "db read failed"}, 500
                else:
                    access_token_url = 'https://api.twitter.com/oauth/access_token'

                    token = oauth.Token(oauth_token, oauth_token_secret)
                    token.set_verifier(request.args.get("oauth_verifier"))
                    
                    consumer_key = os.environ['CONSUMER_KEY']
                    consumer_secret = os.environ['CONSUMER_SECRET']
                    consumer = oauth.Consumer(consumer_key, consumer_secret)

                    client = oauth.Client(consumer, token)

                    resp, content = client.request(access_token_url, "POST")
                    access_token_dict = dict(urllib.parse.parse_qsl(content))

                    access_token = "%s" % access_token_dict['oauth_token'.encode("utf-8")].decode("utf-8")
                    access_token_secret = "%s" % access_token_dict['oauth_token_secret'.encode("utf-8")].decode("utf-8")

                    try:
                        pg_con = psycopg2.connect(pg_connect_info)
                        pg_cur = pg_con.cursor()
                        pg_cur.execute("""UPDATE user_keys SET access_token=%s, access_token_secret=%s WHERE session_current_user=%s""",
                                (access_token, access_token_secret, session["tg_guid"]))

                        pg_con.commit()
                        pg_con.close()
                    except psycopg2.Error as e:
                        print(e)
                        return {"status": "db insert failed"}, 500

                    return { "status": "Authenticated", }, 201
        else:
            return {"status": "Access Denied"}, 403

class verify_twit(Resource):
    def get(self):
        if "tg_guid" in session:
            token = ''
            token_secret = ''

            try:
                pg_con = psycopg2.connect(pg_connect_info)
                pg_cur = pg_con.cursor()
                pg_cur.execute("""SELECT access_token, access_token_secret FROM user_keys WHERE session_current_user=%s""", (session["tg_guid"],))
                pg_ret = pg_cur.fetchone()
                if pg_ret is not None:
                    (token, token_secret) = (pg_ret[0], pg_ret[1])
                pg_con.close()
            except psycopg2.Error as e:
                print(e)
                return {"status": "db lookup failed"}, 200

            if token is not None and token_secret is not None:
                twit_api = twitter.Api(consumer_key=os.environ['CONSUMER_KEY'],
                        consumer_secret=os.environ['CONSUMER_SECRET'],
                        access_token_key=token,
                        access_token_secret=token_secret)

                user = twit_api.VerifyCredentials()
                if user is not None:
                    return {
                            "status": "Authenticated",
                            "twitter_user": user.name,
                            "profile_img_url": user.profile_image_url_https
                            }, 202
                else:
                    return {"status": "twitter auth error"}, 200
            else:
                return {"status": "twitter auth not accepted"}, 200
        else:
            return {"status": "Not Authenticated"}, 200

class sign_out(Resource):
    def get(self):
        try:
            pg_con = psycopg2.connect(pg_connect_info)
            pg_cur = pg_con.cursor()
            pg_cur.execute("""DELETE FROM user_keys WHERE session_current_user=%s""", (session["tg_guid"],))
            pg_con.close()
        except psycopg2.Error as e:
            print(e)
            return {"status": "Sign-out Failed"}, 200

        session.pop('tg_guid', None)
        return {"status": "Signed out"}, 200


api.add_resource(process_user, '/process_user')
api.add_resource(get_results, '/get_results')
api.add_resource(auth_twit, '/auth_twit')
api.add_resource(verify_twit, '/verify_twit')
api.add_resource(get_auth_url, '/get_auth_url')
api.add_resource(sign_out, '/logout')


def validate_searched_user(screen_name=None):
    #timeline = twit_api.GetFavorites(screen_name=screen_name, count=1)
    try: user = twit_api.VerifyCredentials()
    except Exception as e:
        print("Twitter verify malfunctioned")
        print(e)
        return False
    if user is None: return False
    else: return True

def get_user(screen_name=None, offset=0):
    try: int(offset)
    except:
        print(isinstance(offset, int))
        return "invalid offset"
    else:
        if int(offset) < 0:
            return "invalid offset"
        if int(offset) > 500:
            return "offset too large"

    try: pg_con = psycopg2.connect(pg_connect_info)
    except:
        return "db_error"
    else:
        pg_cur = pg_con.cursor(cursor_factory=RealDictCursor)
        pg_cur.execute("""SELECT created_at, user_favorites.post_id, text, name, twitter_posts.screen_name, profile_image_url, possibly_sensitive, post_url, media_url_0, media_url_1, media_url_2, media_url_3, media_url_0_size_x, media_url_1_size_x, media_url_2_size_x, media_url_3_size_x, media_url_0_size_y, media_url_1_size_y, media_url_2_size_y, media_url_3_size_y FROM user_favorites JOIN twitter_posts ON user_favorites.post_id = twitter_posts.post_id WHERE user_favorites.screen_name=%s AND media_url_0 IS NOT NULL ORDER BY (user_favorites.post_id::bigint) DESC LIMIT 20 OFFSET %s;""", (screen_name, int(offset)*20))
        ret = pg_cur.fetchall()
        pg_con.close()

        if len(ret) == 0: return "no more results"
        return ret

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
                pg_cur.execute("""INSERT INTO twitter_posts(created_at, post_id, text, name, screen_name, profile_image_url, possibly_sensitive, post_url) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;""",(str_create_time, favorite.id_str, favorite.text, favorite.user.name, favorite.user.screen_name, favorite.user.profile_image_url, str(favorite.possibly_sensitive), "https://twitter.com/"+favorite.user.screen_name+"/status/"+favorite.id_str)) 
                pg_cur.execute("""INSERT INTO user_favorites(screen_name, post_id) VALUES(%s,%s) ON CONFLICT DO NOTHING""", (screen_name, favorite.id_str))
                try:
                    for index, media in enumerate(favorite.media):
                        media_url = media.media_url
                        id_str = favorite.id_str
                        media_url_size_x = media.sizes['large']['w']
                        media_url_size_y = media.sizes['large']['h']

                        pg_cur.execute("""UPDATE twitter_posts SET media_url_"""+str(index)+"""=%s WHERE post_id=%s;""",(media_url, id_str)) 
                        pg_cur.execute("""UPDATE twitter_posts SET media_url_"""+str(index)+"""_size_x=%s WHERE post_id=%s;""",(media_url_size_x, id_str)) 
                        pg_cur.execute("""UPDATE twitter_posts SET media_url_"""+str(index)+"""_size_y=%s WHERE post_id=%s;""",(media_url_size_y, id_str)) 
                except Exception as e:
                    pass
                else:
                    pg_con.commit()
            # TODO - Add timer before deleting user entry to prevent over-reloading
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

def handler(signum, frame):
    sys.exit(1)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handler)

    #try:
    #    pg_con = psycopg2.connect(pg_connect_info)
    #except:
    #    print("db error")
    #else:
    #    pg_cur = pg_con.cursor()
    #    pg_cur.execute("""DELETE FROM user_status;""")
    #    pg_con.commit()
    #    pg_cur.execute("""DELETE FROM user_favorites;""")
    #    pg_con.commit()
    #    pg_cur.execute("""DELETE FROM twitter_posts;""")
    #    pg_con.commit()
    #    pg_con.close()
    print("Started")
    app.run(host='0.0.0.0')
