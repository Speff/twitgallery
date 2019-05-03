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
    post_url TEXT,
    possibly_sensitive TEXT,
    UNIQUE(post_id)
);

CREATE TABLE user_favorites(
    screen_name TEXT,
    post_id TEXT,
    UNIQUE(screen_name, post_id)
);

CREATE TABLE user_status(
    screen_name TEXT,
    status TEXT
);

CREATE TABLE user_keys(
    session_current_user TEXT,
    access_token TEXT,
    access_token_secret TEXT
);
