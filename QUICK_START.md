# ⚡ Quick Start Guide - Travel Bot

Get the Travel Bot up and running in 15 minutes!

## 🎯 What You'll Need

- ✅ Python 3.8+ installed
- ✅ PostgreSQL database (local or Supabase)
- ✅ Telegram Bot Token (from @BotFather)
- ✅ Google OAuth credentials (for @newuu.uz)
- ✅ ngrok (for local development)
- ✅ 15 minutes of your time

## 🚀 5-Minute Setup

### Step 1: Clone and Install (2 minutes)

```bash
# Clone the repository
cd ~/Documents
git clone <repository-url> "Travel Bot"
cd "Travel Bot"

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment (3 minutes)

Create `.env` file:

```bash
touch .env
```

Add these values (replace with your actual credentials):

```env
# Bot Configuration
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
BOT_USERNAME=putravelbot
URL=https://your-ngrok-url.ngrok-free.app

# Database (Option A: Supabase)
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres

# OR Database (Option B: Local PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_NAME=travel_bot

# Google OAuth
CLIENT_ID=123456789-abcdefgh.apps.googleusercontent.com
CLIENT_SECRET=GOCSPX-your-secret-here
OAUTH_REDIRECT_URI=https://your-ngrok-url.ngrok-free.app/auth/callback

# Admin Telegram IDs (get from @userinfobot)
ADMINS=123456789,987654321
```

### Step 3: Setup Database (2 minutes)

```bash
# Initialize database
python scripts/reset_db.py
```

Expected output:
```
✅ All tables created successfully!
```

### Step 4: Start ngrok (1 minute)

In a **new terminal**:

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

**Update `.env`:**
```env
URL=https://abc123.ngrok-free.app
OAUTH_REDIRECT_URI=https://abc123.ngrok-free.app/auth/callback
```

### Step 5: Start the Bot (1 minute)

Back in the first terminal:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 6: Test It! (1 minute)

1. Open Telegram
2. Find your bot (@putravelbot or your bot username)
3. Send `/start`
4. You should see the registration button!

## ✅ Verification Checklist

Run through this checklist to ensure everything works:

### Backend
- [ ] Application starts without errors
- [ ] Webhook set successfully (check logs)
- [ ] Database connection works
- [ ] Admin dashboard accessible at `https://your-ngrok-url/admin`

### Bot Commands
- [ ] `/start` - Shows registration button
- [ ] `/help` - Shows help message
- [ ] `/menu` - Shows quick menu

### Registration Flow
- [ ] Click "Register with Google"
- [ ] Opens in external browser
- [ ] OAuth flow works
- [ ] Redirects back to bot
- [ ] Bot sends welcome message

### Admin Features
- [ ] Can access `/admin` in browser
- [ ] Can create new trip
- [ ] Trip appears in bot with `/trips`

## 🐛 Common Issues & Quick Fixes

### Issue: "Configuration Error"
```
❌ Error: Missing BOT_TOKEN
```

**Fix**: Check your `.env` file has all required values
```bash
cat .env | grep BOT_TOKEN
```

### Issue: Database Connection Failed
```
❌ Error: could not connect to server
```

**Fix**: 
- **Supabase**: Check your DATABASE_URL is correct
- **Local**: Ensure PostgreSQL is running
```bash
# macOS
brew services start postgresql

# Ubuntu
sudo systemctl start postgresql
```

### Issue: Webhook Not Working
```
Webhook info: {"url": "", "has_custom_certificate": false}
```

**Fix**: Restart the application (webhook sets on startup)
```bash
# Press Ctrl+C to stop
# Then restart
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Issue: ngrok URL Changed
```
❌ Error: 404 Not Found
```

**Fix**: Every time ngrok restarts, update `.env` with new URL
```bash
# 1. Check ngrok terminal for new URL
# 2. Update .env
# 3. Restart application
```

### Issue: OAuth Error "redirect_uri_mismatch"
```
❌ Error: The redirect URI in the request does not match
```

**Fix**: Add redirect URI to Google Cloud Console
1. Go to: https://console.cloud.google.com/apis/credentials
2. Edit your OAuth Client ID
3. Add: `https://your-ngrok-url.ngrok-free.app/auth/callback`
4. Click Save

## 📱 Test the Full Flow

### 1. User Registration
```
User → /start → Register with Google → OAuth → Success → Welcome Message
```

### 2. Create Trip (Admin)
1. Go to `https://your-ngrok-url/admin`
2. Click "Create New Trip"
3. Fill in trip details
4. Submit

### 3. Join Trip (User)
```
User → /trips → Select Trip → Read Terms → Confirm → See Payment Info
```

### 4. Upload Receipt (User)
```
User → Send Photo/PDF → Bot: "Receipt received, marked as 50% paid"
```

### 5. Approve Payment (Admin)
1. Go to `https://your-ngrok-url/admin`
2. Click on trip
3. See member with receipt
4. Click "50%" button
5. User receives invite link

## 🔧 Development Tips

### Hot Reload
The `--reload` flag automatically restarts on file changes:
```bash
uvicorn main:app --reload
```

### Check Logs
Monitor application in real-time:
```bash
# In the terminal where uvicorn is running
# Logs appear automatically
```

### Database Reset
Reset database when needed (⚠️ deletes all data):
```bash
python scripts/reset_db.py
```

### Test Error Handling
Trigger errors to test error messages:
```python
# In bot.py, temporarily add:
raise Exception("Test error")
```

### Check Webhook Status
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

## 📚 Next Steps

### Learn the Codebase
1. Read `README.md` - Full documentation
2. Read `PROJECT_STRUCTURE.md` - File organization
3. Read `ERROR_CODES.md` - Error reference

### Customize the Bot
1. **Change bot commands**: Edit `bot.py`
2. **Modify templates**: Edit files in `templates/`
3. **Add API endpoints**: Create new file in `routers/`
4. **Change database**: Modify models in `models/`

### Deploy to Production
1. Read `DEPLOYMENT.md`
2. Choose hosting (VPS/Heroku/Docker)
3. Setup production database
4. Configure production domain
5. Update Google OAuth redirect URIs
6. Deploy!

## 🆘 Getting Help

### Check Documentation
- `README.md` - General documentation
- `DEPLOYMENT.md` - Deployment guide
- `GOOGLE_OAUTH_SETUP.md` - OAuth setup
- `ERROR_CODES.md` - Error reference

### Debug Checklist
When something doesn't work:
1. ✅ Check terminal logs for errors
2. ✅ Verify `.env` has all values
3. ✅ Confirm database is running
4. ✅ Check ngrok is running
5. ✅ Verify webhook is set
6. ✅ Test bot commands manually

### Common Commands

```bash
# Check if database exists
psql -U postgres -l | grep travel_bot

# Test database connection
python -c "from database import engine; print(engine)"

# Check Python packages
pip list | grep -i telegram

# View environment variables
cat .env

# Check running processes
ps aux | grep python
```

## 🎉 Success!

You should now have:
- ✅ Bot responding to commands
- ✅ Database initialized
- ✅ Webhook working
- ✅ OAuth flow functional
- ✅ Admin dashboard accessible

**Ready to build amazing travel management features!** 🚀

---

## ⏱️ Time Estimates

| Task | Time |
|------|------|
| Installation | 2 min |
| Configuration | 3 min |
| Database Setup | 2 min |
| Start ngrok | 1 min |
| Start Bot | 1 min |
| Testing | 5 min |
| **Total** | **~15 min** |

## 🎓 Learning Resources

### Python & FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

### Telegram Bots
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [pyTelegramBotAPI Docs](https://github.com/eternnoir/pyTelegramBotAPI)
- [Telegram WebApps](https://core.telegram.org/bots/webapps)

### Databases
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/)

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
