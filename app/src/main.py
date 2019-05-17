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

pg_connect_info = "dbname=twitgallery user=tg_user password=docker host=db"

class get_user_statuses(Resource):
    def post(self):
        # Look for session in cookies sent
        if "tg_guid" in session:
            token = ''
            token_secret = ''

            # Look for session cookie data in db
            try:
                pg_con = psycopg2.connect(pg_connect_info)
                pg_cur = pg_con.cursor()
                pg_cur.execute("""SELECT access_token, access_token_secret FROM user_keys WHERE session_current_user=%s""", (session["tg_guid"],))
                pg_ret = pg_cur.fetchone()
                if pg_ret is not None:
                    (token, token_secret) = (pg_ret[0], pg_ret[1])
                else:
                    return {"status": "session not found"}, 200
                pg_con.close()
            except psycopg2.Error as e:
                print(e)
                return {"status": "db error looking up session"}, 200

            # Grab form data
            screen_name = request.form["user_id"]
            offset = request.form["offset"]
            post_type = request.form["type"]

            twit_api_instance = twitter.Api(consumer_key=os.environ['CONSUMER_KEY'],
                    consumer_secret=os.environ['CONSUMER_SECRET'],
                    access_token_key=token,
                    access_token_secret=token_secret)

            query_result = ""

            posts = []
            status_code = 503
            new_offset = offset

            while len(posts) < 20:
                if new_offset == "0":
                    # Validate twitter credentials on first load
                    # Query for initial images
                    # A higher offset implies we already validated credentials
                    if validate_twitter_credentials(twit_api_instance) == False:
                        return {"status": "credentials no longer valid"}, 200
                    query_result = query_twitter_posts(screen_name, twit_api_instance, post_type, new_max=None);

                # Collect user favorites by querying db
                new_offset, user_status, posts_ret = get_posts(screen_name, new_offset, post_type)
                
                if user_status == "no more stored images":
                    pos = int(new_offset);
                    n_db_records, oldest_status_id = get_number_of_statuses(screen_name, post_type)
                    if n_db_records - pos < 40:
                        query_result = query_twitter_posts(screen_name, twit_api_instance, post_type, oldest_status_id);

                        if query_result == "no more posts":
                            if len(posts) == 0:
                                status_code = 204
                                break
                            else:
                                user_status = "end of posts";
                                status_code = 202
                                break

                elif user_status == "db_error":
                    status_code = 503
                    break
                else:
                    posts += posts_ret
                    status_code = 202

            return {
                    "posts": posts,
                    "status": user_status,
                    "last_offset": new_offset,
                    "user_id": screen_name
                    }, status_code
        else:
            return {"status": "session not found"}, 200

class get_auth_url(Resource):
    def get(self):
        if request.method == "GET":
            ret_uuid = str(uuid.uuid4())

            session['tg_guid'] = ret_uuid

            consumer_key = os.environ['CONSUMER_KEY']
            consumer_secret = os.environ['CONSUMER_SECRET']
            consumer = oauth.Consumer(consumer_key, consumer_secret)

            request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=" + os.environ['CALLBACK_URL']
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
                else:
                    pg_con.close()
                    return {"status": "Not authenticated"}
                pg_con.close()
            except psycopg2.Error as e:
                print(e)
                return {"status": "db lookup failed"}, 200

            if token is not None and token_secret is not None:
                twit_api = twitter.Api(consumer_key=os.environ['CONSUMER_KEY'],
                        consumer_secret=os.environ['CONSUMER_SECRET'],
                        access_token_key=token,
                        access_token_secret=token_secret)

                try:
                    user = twit_api.VerifyCredentials()
                except Exception as e:
                    print(e)
                    return {"status": "twitter auth not accepted"}, 200
                else:
                    if user is not None:
                        return {
                                "status": "Authenticated",
                                "twitter_user": user.screen_name,
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


api.add_resource(get_user_statuses, '/get_user_statuses')
api.add_resource(auth_twit, '/auth_twit')
api.add_resource(verify_twit, '/verify_twit')
api.add_resource(get_auth_url, '/get_auth_url')
api.add_resource(sign_out, '/logout')


def validate_twitter_credentials(twit_api_instance=None):
    try: user = twit_api_instance.VerifyCredentials()
    except Exception as e:
        print("Twitter verify malfunctioned")
        print(e)
        return False
    if user is None: return False
    else: return True

def validate_search_user(twit_api_instance=None, screen_name=None):
    try: user = twit_api_instance.VerifyCredentials()
    except Exception as e:
        print("Twitter verify malfunctioned")
        print(e)
        return False
    if user is None: return False
    else: return True

def get_number_of_statuses(screen_name=None, post_type="favorites"):
    try: pg_con = psycopg2.connect(pg_connect_info)
    except:
        return "db_error"
    else:
        pg_cur = pg_con.cursor()
        if post_type == "favorites":
            pg_cur.execute("""SELECT COUNT(*) FROM user_favorites WHERE screen_name=%s;""", (screen_name, ))
        else:
            pg_cur.execute("""SELECT COUNT(*) FROM user_posts WHERE screen_name=%s;""", (screen_name, ))
        count = pg_cur.fetchone()[0]

        if post_type == "favorites":
            pg_cur.execute("""SELECT CAST(post_id AS bigint) FROM user_favorites WHERE screen_name=%s ORDER BY post_id ASC LIMIT 1;""", (screen_name, ))
        else:
            pg_cur.execute("""SELECT CAST(post_id AS bigint) FROM user_posts WHERE screen_name=%s ORDER BY post_id ASC LIMIT 1;""", (screen_name, ))
        oldest_id = pg_cur.fetchone()[0]

        pg_con.close()

        return count, oldest_id

def get_posts(screen_name=None, offset=0, post_type="favorites"):
    try: int(offset)
    except:
        print(isinstance(offset, int))
        return 0, "invalid offset", 0
    else:
        if int(offset) < 0:
            return 0, "invalid offset", 0
        if int(offset) > 5000:
            return 0, "offset too large", 0

    try: pg_con = psycopg2.connect(pg_connect_info)
    except:
        return 0, "db_error", 0
    else:
        pg_cur = pg_con.cursor(cursor_factory=RealDictCursor)

        if post_type == "favorites":
            pg_cur.execute("""SELECT created_at, user_favorites.post_id, text, name, twitter_posts.screen_name, profile_image_url, possibly_sensitive, post_url, media_url_0, media_url_1, media_url_2, media_url_3, media_url_0_size_x, media_url_1_size_x, media_url_2_size_x, media_url_3_size_x, media_url_0_size_y, media_url_1_size_y, media_url_2_size_y, media_url_3_size_y FROM user_favorites JOIN twitter_posts ON user_favorites.post_id = twitter_posts.post_id WHERE user_favorites.screen_name=%s ORDER BY (user_favorites.post_id::bigint) DESC LIMIT 20 OFFSET %s;""", (screen_name, int(offset)))
        else:
            pg_cur.execute("""SELECT created_at, user_posts.post_id, text, name, twitter_posts.screen_name, profile_image_url, possibly_sensitive, post_url, media_url_0, media_url_1, media_url_2, media_url_3, media_url_0_size_x, media_url_1_size_x, media_url_2_size_x, media_url_3_size_x, media_url_0_size_y, media_url_1_size_y, media_url_2_size_y, media_url_3_size_y FROM user_posts JOIN twitter_posts ON user_posts.post_id = twitter_posts.post_id WHERE user_posts.screen_name=%s ORDER BY (user_posts.post_id::bigint) DESC LIMIT 20 OFFSET %s;""", (screen_name, int(offset)))

        posts = pg_cur.fetchall()

        if len(posts) == 0: 
            return offset, "no more stored images", 0

        last_offset = str(int(offset) + len(posts))

        posts[:] = [post for post in posts if post["media_url_0"] is not None] 

        pg_con.close()
        return last_offset, "got posts", posts

def query_twitter_posts(screen_name=None, twit_api_instance=None, post_type="favorites", new_max=None):
    print("Querying twitter")
    try: pg_con = psycopg2.connect(pg_connect_info)
    except:
        return "db access failure"
    else:
        try:
            if post_type == "favorites":
                if new_max is not None:
                    posts = twit_api_instance.GetFavorites(screen_name=screen_name, max_id=new_max-1, count=200)
                else:
                    posts = twit_api_instance.GetFavorites(screen_name=screen_name, count=200)
            elif post_type == "posts":
                if new_max is not None:
                    posts = twit_api_instance.GetUserTimeline(screen_name=screen_name, max_id=new_max-1, count=200, include_rts=False)
                else:
                    posts = twit_api_instance.GetUserTimeline(screen_name=screen_name, count=200, include_rts=False)
            else:
                raise Exception('wtf you sending me')
        except Exception as e:
            print(e)
            pg_cur = pg_con.cursor()
            pg_cur.execute("""DELETE FROM user_status WHERE screen_name=%s;""", (screen_name,))
            pg_con.commit()
            pg_con.close()
            return "twitter_lookup_failed"
        else:
            if len(posts) == 0:
                return "no more posts"
            pg_cur = pg_con.cursor()
            for post in posts:
                create_time = datetime.strptime(post.created_at, '%a %b %d %H:%M:%S +0000 %Y')
                str_create_time = create_time.strftime("%m/%d/%Y, %H:%M:%S")
                pg_cur.execute("""INSERT INTO twitter_posts(created_at, post_id, text, name, screen_name, profile_image_url, possibly_sensitive, post_url) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;""",(str_create_time, post.id_str, post.text, post.user.name, post.user.screen_name, post.user.profile_image_url, str(post.possibly_sensitive), "https://twitter.com/"+post.user.screen_name+"/status/"+post.id_str)) 
                if post_type == "favorites":
                    pg_cur.execute("""INSERT INTO user_favorites(screen_name, post_id) VALUES(%s,%s) ON CONFLICT DO NOTHING""", (screen_name, post.id_str))
                elif post_type == "posts":
                    pg_cur.execute("""INSERT INTO user_posts(screen_name, post_id) VALUES(%s,%s) ON CONFLICT DO NOTHING""", (screen_name, post.id_str))
                try:
                    for index, media in enumerate(post.media):
                        media_url = media.media_url
                        id_str = post.id_str
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

    return "success"

def check_user_status(screen_name=None):
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
    #    pg_cur.execute("""DELETE FROM user_posts;""")
    #    pg_con.commit()
    #    pg_cur.execute("""DELETE FROM twitter_posts;""")
    #    pg_con.commit()
    #    pg_con.close()
    print("Started")
    #app.run(host='0.0.0.0')
