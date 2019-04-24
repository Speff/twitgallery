CREATE TABLE twitter_posts(
    created_at TEXT,
    post_id TEXT,
    text TEXT,
    name TEXT,
    screen_name TEXT,
    profile_image_url TEXT,
    media_url_0 TEXT,
    media_url_1 TEXT,
    media_url_2 TEXT,
    media_url_3 TEXT,
    post_url TEXT
);

CREATE TABLE user_favorites(
    screen_nme TEXT,
    post_id TEXT
);

CREATE TABLE user_status(
    screen_name TEXT,
    status TEXT
);

CREATE TABLE user_keys(
    user TEXT,
    access_token text,
    access_token_secret text
)
