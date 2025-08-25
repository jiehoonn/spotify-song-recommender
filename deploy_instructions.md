# 🚀 Deployment Guide - Song Recommender

## Quick Deploy to Railway (Recommended)

### 1. Install Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Or with curl
curl -fsSL https://railway.app/install.sh | sh
```

### 2. Deploy Your App

```bash
# Login to Railway
railway login

# Initialize project
railway init

# Add PostgreSQL database
railway add postgresql

# Deploy your app
railway up

# Get your app URL
railway domain
```

### 3. Set Environment Variables

In Railway dashboard or via CLI:

```bash
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY="your-super-secret-key-here"
railway variables set PYTHONPATH=/app
```

### 4. Setup Database Tables

After deployment, run this once:

```bash
railway run python src/database/setup_production.py
```

---

## Alternative: Heroku Deployment

### 1. Install Heroku CLI

```bash
# Install Heroku CLI (https://devcenter.heroku.com/articles/heroku-cli)
# Then login
heroku login
```

### 2. Create Heroku App

```bash
# Create app
heroku create your-song-recommender

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY="your-super-secret-key-here"

# Deploy
git add .
git commit -m "Deploy song recommender"
git push heroku main

# Setup database
heroku run python src/database/setup_production.py
```

---

## Alternative: DigitalOcean App Platform

### 1. Create GitHub Repository

```bash
# Push your code to GitHub
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. DigitalOcean Setup

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn --bind 0.0.0.0:$PORT src.web.app:app`
   - **Environment Variables**:
     - `FLASK_ENV=production`
     - `SECRET_KEY=your-secret-key`

### 3. Add Database

1. Add PostgreSQL database component
2. Note the connection string
3. Run setup: `python src/database/setup_production.py`

---

## Environment Variables Needed

```bash
# Required for all platforms
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# Database (automatically set by Railway/Heroku)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Optional (for future API integrations)
LASTFM_API_KEY=your-key
SPOTIFY_CLIENT_ID=your-id
SPOTIFY_CLIENT_SECRET=your-secret
```

---

## Post-Deployment Checklist

### 1. Verify Deployment

- [ ] App loads at your domain
- [ ] Database tables exist
- [ ] Admin dashboard accessible at `/admin`

### 2. Test Core Functionality

- [ ] Browse songs at `/`
- [ ] Get recommendations for a song
- [ ] Submit feedback (Like/Dislike)
- [ ] Check admin stats show feedback

### 3. Test Active Learning

- [ ] Submit 15+ feedback samples
- [ ] Model automatically trains
- [ ] Recommendations switch to "Active Learning" mode

### 4. Monitor System

- [ ] Check `/admin/stats` for real-time metrics
- [ ] Verify feedback is stored in database
- [ ] Watch model accuracy improve over time

---

## Troubleshooting

### Common Issues:

**"No module named 'src'"**

```bash
# Set PYTHONPATH environment variable
PYTHONPATH=/app
```

**Database connection errors**

```bash
# Check DATABASE_URL is set correctly
echo $DATABASE_URL

# Verify database tables exist
python src/database/setup_production.py
```

**Import errors in production**

```bash
# Ensure all dependencies in requirements.txt
pip freeze > requirements.txt
```

### Debug Commands:

```bash
# Check environment variables
env | grep -E "(DATABASE_URL|FLASK_ENV|SECRET_KEY)"

# Test database connection
python -c "from src.database.connection import engine; print('✅ DB Connected')"

# Check app startup
python src/web/app.py
```

---

## Success Indicators

✅ **Your app is working when:**

- Users can visit your public URL
- Songs load on the homepage
- Users can click "Recommend" and get suggestions
- Feedback buttons (Like/Dislike) work
- Admin dashboard shows statistics
- Feedback counts increase in `/admin/stats`

🎯 **Active learning working when:**

- After 15+ feedback samples, model trains automatically
- Recommendations show "Active Learning" instead of "Baseline"
- Model accuracy visible in admin dashboard
- Different recommendations than baseline model
