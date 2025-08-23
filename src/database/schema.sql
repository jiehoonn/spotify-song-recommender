-- SONGS TABLE 
CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    lastfm_mbid VARCHAR(64),
    lastfm_title VARCHAR(255),
    lastfm_artist VARCHAR(255),
    lastfm_url TEXT,
    lastfm_playcount INTEGER,
    lastfm_listeners INTEGER,
    spotify_id VARCHAR(64) UNIQUE,
    spotify_title VARCHAR(255),
    spotify_artist VARCHAR(255),
    spotify_album VARCHAR(255),
    spotify_popularity INTEGER,
    spotify_duration_ms INTEGER,
    spotify_url TEXT,
    reccobeats_id VARCHAR(64),
    acousticness FLOAT,
    danceability FLOAT,
    energy FLOAT,
    instrumentalness FLOAT,
    liveness FLOAT,
    loudness FLOAT,
    speechiness FLOAT,
    tempo FLOAT,
    valence FLOAT,
    popularity INTEGER,
    lastfm_tag_counts JSONB
);

-- LYRICS TABLE
CREATE TABLE lyrics (
    id SERIAL PRIMARY KEY,
    song_id INTEGER UNIQUE REFERENCES songs(id),
    cleaned_lyrics TEXT
);

-- SONG EMOTION SCORES TABLE
CREATE TABLE song_emotion_scores (
    id SERIAL PRIMARY KEY,
    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
    emotion VARCHAR(32),
    score FLOAT,
    total_words INTEGER,
    matched_words INTEGER,
    CONSTRAINT uix_song_emotion UNIQUE (song_id, emotion)
);

-- SONG LYRIC EMBEDDINGS TABLE
CREATE TABLE song_lyric_embeddings (
    id SERIAL PRIMARY KEY,
    song_id INTEGER UNIQUE REFERENCES songs(id) ON DELETE CASCADE,
    embedding FLOAT[],  -- Stores the vector as a float array
    model_name VARCHAR(128),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- USER FEEDBACK TABLE
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR,
    source_song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
    recommended_song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
    feedback VARCHAR,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);