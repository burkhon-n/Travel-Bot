# 🏠 Local Development Setup

## 📋 Prerequisites

- Python 3.9 or higher
- PostgreSQL database (or Supabase)
- Telegram Bot Token (from @BotFather)
- Google OAuth credentials

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (if not exists)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_from_botfather
BOT_USERNAME=YourBotUsername
URL=http://localhost:8000

# Admin User IDs (comma-separated Telegram IDs)
ADMINS=123456789,987654321

# Google OAuth
CLIENT_ID=your_google_client_id.apps.googleusercontent.com
CLIENT_SECRET=your_google_client_secret
REDIRECT_URI=http://localhost:8000/auth/callback

# Database (PostgreSQL/Supabase)
DATABASE_URL=postgresql://user:password@host:port/database

# Development Settings
BYPASS_TELEGRAM_CHECK=true
STRICT_TELEGRAM_CHECK=false
```

### 3. Initialize Database

```bash
# Run database reset script (creates tables)
python scripts/reset_db.py
```

### 4. Run the Application

**Option 1: Using the run script (recommended)**
```bash
./run_local.sh
```

**Option 2: Using uvicorn directly**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Using Python module**
```bash
python -m uvicorn main:app --reload
```

### 5. Access the Application

- **Homepage**: http://localhost:8000/home
- **Privacy Policy**: http://localhost:8000/privacy
- **API Info**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin (with BYPASS_TELEGRAM_CHECK=true)

## 🔧 Development Configuration

### Local vs Production Settings

**For Local Development:**
```env
URL=http://localhost:8000
REDIRECT_URI=http://localhost:8000/auth/callback
BYPASS_TELEGRAM_CHECK=true
STRICT_TELEGRAM_CHECK=false
```

**For Production (Render):**
```env
URL=https://your-app.onrender.com
REDIRECT_URI=https://your-app.onrender.com/auth/callback
BYPASS_TELEGRAM_CHECK=false
STRICT_TELEGRAM_CHECK=true
```

### Google OAuth Setup for Localhost

In Google Cloud Console:
1. Go to APIs & Services → Credentials
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized JavaScript origins**:
   - `http://localhost:8000`
4. Add to **Authorized redirect URIs**:
   - `http://localhost:8000/auth/callback`

### Telegram Bot Webhook

**For local development**, you have two options:

**Option 1: Use ngrok (recommended)**
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Update .env:
URL=https://abc123.ngrok.io
REDIRECT_URI=https://abc123.ngrok.io/auth/callback

# Set webhook
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://abc123.ngrok.io/webhook/<YOUR_TOKEN>"
```

**Option 2: Delete webhook (polling mode)**
```bash
# Remove webhook for local testing
curl "https://api.telegram.org/bot<YOUR_TOKEN>/deleteWebhook"

# Bot won't receive updates in real-time
# You'll need to manually trigger endpoints
```

## 🧪 Testing Locally

### Test Public Pages
```bash
# Should return HTML
curl http://localhost:8000/home
curl http://localhost:8000/privacy
```

### Test API
```bash
# Should return JSON
curl http://localhost:8000/
```

### Test Admin (with BYPASS_TELEGRAM_CHECK=true)
```bash
# Should work in browser
open http://localhost:8000/admin
```

### Test Telegram Integration
1. Use ngrok to get public URL
2. Set webhook to ngrok URL
3. Send `/start` to your bot in Telegram
4. Bot should respond

## 🐛 Debugging

### Enable Debug Logging

In `utils/logging_config.py`, change:
```python
def setup_logging(level: int = logging.DEBUG):  # Changed from INFO
```

### Check Database Connection
```bash
python -c "from database import engine; print(engine.connect())"
```

### Verify Bot Token
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### Check Webhook Status
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

## 📁 Project Structure

```
Travel Bot/
├── main.py                 # FastAPI application
├── bot.py                  # Telegram bot instance
├── config.py               # Configuration management
├── database.py             # Database connection
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .env.example           # Example environment file
│
├── routers/               # API routes
│   ├── webhook.py         # Telegram webhook
│   ├── auth.py            # Google OAuth
│   ├── webapp.py          # Web app pages
│   ├── trips.py           # Trip management
│   └── admin.py           # Admin dashboard
│
├── models/                # Database models
│   ├── User.py
│   ├── Trip.py
│   └── TripMember.py
│
├── templates/             # HTML templates
│   ├── home.html
│   ├── privacy.html
│   ├── admin_dashboard.html
│   └── ...
│
├── utils/                 # Utilities
│   ├── logging_config.py
│   └── text_utils.py
│
└── scripts/               # Utility scripts
    └── reset_db.py
```

## 🔄 Hot Reload

The `--reload` flag enables automatic restart when you modify code:
```bash
uvicorn main:app --reload
```

Changes to these files will trigger reload:
- `main.py`
- All files in `routers/`
- All files in `models/`
- Template files (may need manual browser refresh)

## 🚦 Common Issues

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn main:app --reload --port 8001
```

### Database Connection Failed
- Check DATABASE_URL format
- Verify database is running
- Check firewall/network settings
- For Supabase: Allow connections from your IP

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Templates Not Found
- Ensure `templates/` directory exists
- Check file names match exactly
- Restart server after template changes

## 🎯 Development Workflow

1. **Make changes** to code
2. **Server auto-reloads** (with --reload flag)
3. **Test in browser** or with curl
4. **Check logs** in terminal
5. **Repeat!**

## 📊 Performance Tips

### Database Connection Pooling
```python
# In database.py, add pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)
```

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_data():
    # Expensive operation
    pass
```

## 🆘 Getting Help

If you encounter issues:

1. **Check logs** in terminal
2. **Verify .env** file has all required variables
3. **Test database** connection
4. **Check port** is not in use
5. **Review error** messages carefully

## ✅ Ready for Local Development!

Start the server:
```bash
./run_local.sh
```

Happy coding! 🚀
