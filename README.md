# PlaylistAI - Intelligent Playlist Generation

A machine learning-powered playlist recommendation system that outperforms Spotify's algorithm through intelligent flow optimization, transparency, and user control. Built on a $100 student budget.

## 🎯 Project Overview

PlaylistAI creates superior playlists by focusing on:

- **Playlist Flow Optimization**: Smooth song transitions and energy curves
- **Transparent Recommendations**: Users understand why each song was chosen
- **Granular Control**: Fine-tune discovery vs familiarity balance
- **Context Awareness**: Adapts to time, mood, and activity
- **Real-time Learning**: Incorporates user feedback immediately

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Spotify Developer Account (free)
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/spotify-song-recommender.git
cd spotify-song-recommender

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Spotify API credentials
```

### Running the Application

```bash
# Start the Streamlit app
streamlit run src/app.py

# Or run data collection
python src/data_loader.py
```

## 📋 Task Tracking

This project uses a comprehensive task tracking system in `TASKS.md`. All development tasks are organized by phase and tracked with clear deliverables.

### Updating Task Status

Use the built-in utility script to update task progress:

```bash
# Start working on a task
python update_task.py SETUP-001 start

# Complete a task
python update_task.py SETUP-001 complete abc123

# Cancel a task
python update_task.py SETUP-001 cancel
```

### Current Progress

- **Total Tasks**: 44
- **Completed**: 0
- **In Progress**: 0
- **Not Started**: 44

See `TASKS.md` for detailed task breakdown and progress tracking.

## 🏗️ Architecture

### Core Components

- **Data Loader** (`src/data_loader.py`): Spotify API integration and data collection
- **Feature Engineering** (`src/feature_engineering.py`): Audio feature processing
- **Model** (`src/model.py`): ML algorithms for recommendations
- **Recommender** (`src/recommend.py`): Main playlist generation logic

### Technology Stack

- **Python 3.9+**: Main language
- **SQLite**: Local database (free)
- **Streamlit**: Web interface (free hosting)
- **Spotify API**: Music data source (free tier)
- **scikit-learn**: ML algorithms (free)
- **pandas/numpy**: Data processing (free)

## 💰 Budget Constraints

This project is designed for a $100 student budget:

- Domain name: $12/year
- Hosting: Free (Streamlit Cloud)
- Database: Free (SQLite)
- APIs: Free tiers
- Computing: Local development + Google Colab

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/

# Run specific test file
python -m pytest tests/test_similarity.py
```

## 📊 Development Phases

1. **Foundation** (Weeks 1-2): Setup, data collection, basic infrastructure
2. **Core Algorithms** (Weeks 3-4): Similarity, transitions, optimization
3. **Integration** (Weeks 5-6): Core engine, user feedback
4. **Interface** (Weeks 7-8): Web UI, user controls
5. **Quality** (Weeks 9-10): Testing, metrics, validation
6. **Deployment** (Weeks 11-12): Production setup, optimization

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
DATABASE_URL=sqlite:///playlist_ai.db
```

### Database Setup

```bash
# Create database schema
python src/database/setup.py

# Run migrations
python src/database/migrate.py
```

## 📈 Performance Targets

- **Recommendation Generation**: <200ms
- **Database Queries**: <50ms
- **API Response Time**: <500ms
- **Memory Usage**: <512MB
- **Dataset Size**: 1M+ songs

## 🤝 Contributing

1. Check `TASKS.md` for available tasks
2. Create feature branch: `git checkout -b feature/task-id`
3. Implement task following Cursor Rules patterns
4. Update task status: `python update_task.py TASK-ID complete`
5. Commit with task reference: `git commit -m "TASK-ID: Description"`
6. Push and create PR

## 📝 Documentation

- **Task Tracking**: `TASKS.md` - Complete task breakdown and progress
- **Cursor Rules**: `.cursor/rules/` - Development patterns and guidelines
- **API Documentation**: `docs/api.md` - API endpoints and usage
- **Algorithm Design**: `docs/algorithms.md` - ML model architecture

## 🔮 Future Enhancements

### Tier 1 ($1,000 budget)

- Deep learning models
- Real-time audio analysis
- Advanced NLP for lyrics
- Mobile app development

### Tier 2 ($10,000 budget)

- Large-scale data collection
- Real-time streaming integration
- Social features
- Advanced audio ML

### Tier 3 ($100,000 budget)

- Proprietary audio analysis
- Real-time collaboration
- Artist analytics dashboard
- Global music database

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🙏 Acknowledgments

- Spotify Web API for music data
- Open source ML libraries
- Academic research in music recommendation
- University support and resources

---

**Current Status**: Development Phase 1 - Foundation  
**Next Milestone**: Complete Setup & Infrastructure Tasks  
**Last Updated**: 2025-07-13
