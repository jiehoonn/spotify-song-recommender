# Spotify Song Recommender

## Project Overview

This project aims to build a song recommender system using a combination of lyrics-based emotion analysis and audio features. The system is designed to be modular and extensible, with a focus on transparency and iterative improvement. This README serves as a log of our database schema, data collection and cleaning process, baseline modeling approach, and ongoing insights and updates.

---

## Database Tables

### `songs`

- **id**: Primary key
- **spotify_title**: Song title from Spotify
- **spotify_artist**: Artist name from Spotify
- **danceability, energy, valence, acousticness, instrumentalness, liveness, speechiness, tempo**: Audio features from Spotify
- _(other metadata columns as needed)_

### `lyrics`

- **id**: Primary key
- **song_id**: Foreign key to `songs.id`
- **cleaned_lyrics**: Lyrics text, cleaned and preprocessed

### `song_emotion_scores`

- **id**: Primary key
- **song_id**: Foreign key to `songs.id`
- **emotion**: Emotion label (e.g., anger, joy, trust, etc.)
- **score**: Normalized NRC lexicon intensity score for that emotion

---

## Data Collection and Cleaning

- **APIs Used**:

  - Last.fm to retrieve top songs in the charts
  - Reccobeats to retrieve song audio features
  - Spotify API for song metadata
  - Genius API for lyrics

- **Cleaning Process for Lyrics:**
  - Lyrics are lowercased, section headers and non-lyric content are removed, and punctuation is stripped (except apostrophes and newlines).
  - Only English lyrics are retained.
  - NRC lexicon scoring is normalized by total word count in the lyrics.

---

## Baseline Model: `baseline_modelv1.py`

- **Purpose:**  
  A basic content-based recommender that finds similar songs using cosine similarity on concatenated vectors of NRC emotion scores and normalized audio features.

- **How it works:**

  1. Loads all songs and their feature vectors (emotion scores + normalized audio features).
  2. User enters a song title in the terminal.
  3. The script computes cosine similarity between the selected song and all others.
  4. Returns the top 5 most similar songs, displaying their titles, artists, and similarity scores.

- **Interactivity:**
  - Users can browse available songs in the database.
  - For each recommendation, the script prints the feature vectors contributing to the similarity calculation.

---

## Problems and Limitations of the Baseline Model

- **Feature Dominance:**

  - Some features (e.g., "speechiness" or "instrumentalness") are heavily skewed and may disproportionately influence similarity, even after normalization.
  - No weighting is applied between emotion and audio features, so all features are treated as equally important, which may not reflect their true impact on perceived similarity.

- **Limited Emotion Representation:**

  - NRC lexicon covers only a subset of words and emotions; songs with sparse or metaphorical lyrics may have low or zero emotion scores.
  - Emotion scores may not capture the full semantic or thematic content of lyrics.

- **Collinearity:**

  - Audio features like "danceability," "energy," and "valence" can be correlated, potentially causing redundancy in the similarity calculation.

- **Narrow Feature Set:**

  - Only basic audio features and NRC emotion scores are used. No genre, release year, popularity, or user context is considered.

- **Similarity Score Interpretation:**
  - High similarity scores may not always correspond to true musical or emotional similarity, due to the above issues.

---

## Baseline Model v2: Hybrid Song Recommender

**New in v2.0:**

- **Lyric Embeddings:**  
  Each song’s lyrics are embedded using Sentence-BERT (`all-mpnet-base-v2`), capturing semantic and thematic meaning beyond simple word counts.
- **Popularity Integration:**  
  Spotify’s popularity score (0–100, normalized) is now included as a feature, so more popular songs have a slight influence on similarity.
- **Last.fm Tag Integration:**  
  Top tags for each track are fetched from Last.fm, including tag counts (how many users applied each tag). Tag similarity is computed using a weighted Jaccard index.
- **Weighted Hybrid Similarity:**  
  The similarity score is now a weighted sum of:
  - Lyrics embedding similarity (**0.42**)
  - Audio feature similarity (**0.25**)
  - Emotion score similarity (**0.17**)
  - Popularity similarity (**0.08**)
  - Tag similarity (**0.08**)
    All weights sum to 1.0 for interpretability.
- **Robust to Missing Data:**  
  If a song is missing a feature (e.g., no tags or popularity), the similarity calculation automatically adjusts the weights to use only available features.

**How it works:**

- Loads all songs and their feature vectors (lyrics embedding, audio, emotion, popularity, tags).
- User enters a song title in the terminal.
- The script computes a hybrid similarity score between the selected song and all others, using a weighted sum of cosine similarities (for vectors) and weighted Jaccard (for tags).
- Returns the top 5 most similar songs, displaying their titles, artists, and similarity scores.
- Users can also browse available songs in the database.

---

## Update Log

- **v1.0:**
  - Established database schema and data collection pipeline.
  - Implemented baseline content-based recommender using NRC emotion scores and audio features.
  - Added interactive terminal interface for song similarity search and browsing.
  - Documented known issues and areas for improvement.

---

## Next Steps

- Experiment with feature weighting and dimensionality reduction (e.g., PCA).
- Incorporate additional features (genre, year, popularity, etc.).
- Explore lyric embeddings (TF-IDF, word2vec, BERT) for richer text representation.
- Collect and integrate user feedback for personalized recommendations.
- Evaluate model performance with user studies or offline metrics.

---

_This README will be updated as new versions and improvements are made to the system._
