# Vercel Deployment Fix - Summary

## Changes Made to Fix Build

### 1. Created `api/index.py` (Vercel Entry Point)
```python
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from mangum import Mangum

# Vercel serverless handler using Mangum adapter
# Mangum converts ASGI (FastAPI) to AWS Lambda/Vercel format
handler = Mangum(app, lifespan="off")
```

**Key Fix:** Using `Mangum` adapter to convert FastAPI (ASGI) to serverless handler format.
This fixes the `TypeError: issubclass() arg 1 must be a class` error.

### 2. Updated `vercel.json`
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

Points to the new API directory structure.

### 3. Created `runtime.txt`
```
python-3.9
```

Specifies Python version for Vercel.

### 4. Added `mangum` to `requirements.txt`
```
mangum
```

Mangum is an adapter that allows ASGI applications (FastAPI, Starlette) to run on AWS Lambda and Vercel serverless functions.

### 5. Created `.vercelignore`
Excludes unnecessary files from deployment to reduce build size.

### 6. Updated `main.py`
Added serverless detection and conditional lifecycle events:
```python
# Check if running on Vercel (serverless environment)
IS_VERCEL = os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

# Only run startup/shutdown events when NOT on serverless
if not IS_VERCEL:
    @app.on_event('startup')
    async def startup():
        await initialize_bot()
```

**Why:** Serverless functions don't support lifecycle events. They're stateless and cold-start on each invocation.

## Deployment Steps

1. **Commit all changes:**
   ```bash
   git add .
   git commit -m "Fix Vercel deployment configuration"
   git push origin main
   ```

2. **Redeploy on Vercel:**
   - Vercel should auto-deploy when you push
   - Or manually trigger redeploy in Vercel dashboard

3. **Verify Environment Variables** in Vercel dashboard:
   - BOT_TOKEN
   - BOT_USERNAME
   - URL (your Vercel domain)
   - CLIENT_ID
   - CLIENT_SECRET
   - REDIRECT_URI
   - DATABASE_URL
   - ADMINS
   - STRICT_TELEGRAM_CHECK=true

## Common Build Issues & Solutions

### Issue: "No module named 'X'"
**Solution:** Make sure all dependencies are in `requirements.txt`

### Issue: "Build timed out"
**Solution:** 
- Remove unnecessary files via `.vercelignore`
- Make sure database connection doesn't block startup
- Consider making startup events non-blocking

### Issue: "Function size too large"
**Solution:**
- Add more items to `.vercelignore`
- Remove dev dependencies
- Consider splitting into multiple functions

### Issue: "Environment variables not found"
**Solution:**
- Set all required env vars in Vercel dashboard
- Don't commit `.env` file to git
- Use Vercel's environment variable UI

## Testing After Deployment

### Test Public Pages:
```bash
curl https://your-domain.vercel.app/home
curl https://your-domain.vercel.app/privacy
```

Should return HTML pages.

### Test Protected Pages:
```bash
curl https://your-domain.vercel.app/admin
```

Should return "Telegram Required" error page.

### Test API:
```bash
curl https://your-domain.vercel.app/
```

Should return JSON with API information.

## Vercel Logs

If deployment still fails:
1. Go to Vercel Dashboard
2. Click on your project
3. Go to "Deployments"
4. Click on the failed deployment
5. Check "Build Logs" for specific error messages
6. Check "Function Logs" for runtime errors

## Important Notes

- **Serverless Limitations:** Vercel functions have execution time limits (10s on free plan, 60s on pro)
- **Cold Starts:** First request may be slow due to function initialization
- **Stateless:** Each request may run on a different instance
- **Database:** Make sure your Supabase DB allows external connections
- **Webhook:** Bot webhook should point to your Vercel URL

## File Structure for Vercel

```
Travel Bot/
├── api/
│   └── index.py          # Vercel entry point
├── routers/              # API routes
├── models/               # Database models
├── templates/            # Jinja2 templates
├── utils/                # Utilities
├── main.py               # FastAPI app
├── requirements.txt      # Dependencies
├── runtime.txt           # Python version
├── vercel.json          # Vercel config
└── .vercelignore        # Exclude files
```

## Next Steps

1. Push changes to GitHub
2. Wait for Vercel auto-deployment
3. Check deployment logs
4. Test endpoints
5. Update bot webhook URL in Telegram
6. Test from Telegram bot

If issues persist, check Vercel build logs for specific error messages.
