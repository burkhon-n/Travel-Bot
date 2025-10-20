# Vercel Deployment Checklist ✅

## Before Deploying

- [ ] All code changes committed to git
- [ ] `.env` file is in `.gitignore` (never commit secrets!)
- [ ] All dependencies listed in `requirements.txt`
- [ ] `runtime.txt` specifies Python version
- [ ] `vercel.json` configured correctly
- [ ] `api/index.py` exists and imports main app

## Environment Variables to Set in Vercel

Go to: **Vercel Dashboard → Your Project → Settings → Environment Variables**

### Required Variables:
- [ ] `BOT_TOKEN` - Your Telegram bot token from @BotFather
- [ ] `BOT_USERNAME` - Your bot username (e.g., YourTravelBot)
- [ ] `URL` - Your Vercel deployment URL (e.g., https://your-app.vercel.app)
- [ ] `CLIENT_ID` - Google OAuth client ID
- [ ] `CLIENT_SECRET` - Google OAuth client secret
- [ ] `REDIRECT_URI` - OAuth callback (e.g., https://your-app.vercel.app/auth/callback)
- [ ] `DATABASE_URL` - PostgreSQL connection string from Supabase
- [ ] `ADMINS` - Comma-separated admin Telegram user IDs (e.g., 123456789,987654321)

### Optional Variables:
- [ ] `STRICT_TELEGRAM_CHECK` - Set to `true` (default, recommended)
- [ ] `BYPASS_TELEGRAM_CHECK` - Set to `false` (default, recommended)

## After Deployment

### 1. Verify Deployment Success
- [ ] Check Vercel dashboard shows "Ready"
- [ ] No errors in build logs
- [ ] Function deployed successfully

### 2. Test Public Endpoints
- [ ] Visit `https://your-domain.vercel.app/home` - Should show homepage
- [ ] Visit `https://your-domain.vercel.app/privacy` - Should show privacy policy
- [ ] Visit `https://your-domain.vercel.app/` - Should return JSON API info

### 3. Test Protected Endpoints
- [ ] Visit `https://your-domain.vercel.app/admin` in browser - Should show "Telegram Required"
- [ ] Visit `https://your-domain.vercel.app/webapp/register` - Should show "Telegram Required"

### 4. Update Telegram Bot Webhook
Run this command or visit the URL:
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-domain.vercel.app/webhook/<YOUR_BOT_TOKEN>
```

Or visit:
```
https://your-domain.vercel.app/webhook/
```

- [ ] Webhook set successfully
- [ ] Webhook URL points to your Vercel deployment

### 5. Test from Telegram
- [ ] Open bot in Telegram
- [ ] Send `/start` command
- [ ] Click registration button - Should work
- [ ] Send `/admin` (if you're admin) - Should open admin panel
- [ ] Create test trip - Should work
- [ ] Register for trip - Should work
- [ ] Upload payment receipt - Should work

### 6. Update Google OAuth
In Google Cloud Console → APIs & Services → Credentials:

- [ ] Add `https://your-domain.vercel.app` to Authorized JavaScript origins
- [ ] Add `https://your-domain.vercel.app/auth/callback` to Authorized redirect URIs
- [ ] Update Application Home Page to `https://your-domain.vercel.app/home`
- [ ] Update Privacy Policy URL to `https://your-domain.vercel.app/privacy`

### 7. Monitor for Issues
- [ ] Check Vercel function logs for errors
- [ ] Test user registration flow
- [ ] Test payment upload flow
- [ ] Test admin functions
- [ ] Monitor database connections

## Troubleshooting

### Build Fails
1. Check Vercel build logs
2. Verify all files are committed
3. Check `requirements.txt` for missing dependencies
4. Ensure `api/index.py` exists
5. Check `vercel.json` configuration

### Runtime Errors
1. Check Vercel function logs
2. Verify environment variables are set
3. Test database connection (Supabase allows external connections?)
4. Check bot token is valid
5. Verify webhook URL is correct

### "Telegram Required" Showing for Telegram Users
1. Make sure accessing through bot buttons, not direct URL
2. Check `STRICT_TELEGRAM_CHECK` is set correctly
3. Verify Telegram WebApp SDK is working
4. Check browser console for JavaScript errors

### Admin Panel Not Working
1. Verify your Telegram user ID is in `ADMINS` env variable
2. Access through bot `/admin` command, not direct URL
3. Check browser console for errors
4. Verify you're using Telegram WebApp (not regular browser)

### OAuth Not Working
1. Check Google Cloud Console redirect URIs match Vercel URL
2. Verify `CLIENT_ID` and `CLIENT_SECRET` are correct
3. Check `REDIRECT_URI` env variable matches Google settings
4. Test OAuth flow from Telegram (not browser)

## Post-Deployment Commands

### Set Bot Commands Menu:
The startup event should do this automatically, but if needed:
```bash
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setMyCommands \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "start", "description": "Start and register"},
      {"command": "menu", "description": "Open main menu"},
      {"command": "trips", "description": "Browse trips"},
      {"command": "stats", "description": "View live stats"},
      {"command": "mystatus", "description": "My registration/payment"},
      {"command": "help", "description": "How to use the bot"},
      {"command": "admin", "description": "Open admin tools"}
    ]
  }'
```

### Check Webhook Status:
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

### Delete Webhook (if needed):
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook
```

## Success Indicators ✅

- ✅ Vercel shows "Ready" status
- ✅ Public pages accessible from browser
- ✅ Protected pages show "Telegram Required" in browser
- ✅ Bot responds to `/start` command
- ✅ Registration flow works through Telegram
- ✅ Admin panel accessible through bot
- ✅ Payment uploads work
- ✅ No errors in Vercel logs
- ✅ Database connections working
- ✅ OAuth flow completes successfully

## Support

If you encounter issues:
1. Check VERCEL_FIX.md for detailed solutions
2. Review Vercel build and function logs
3. Test locally with `uvicorn main:app --reload`
4. Check Telegram bot logs
5. Verify all environment variables
6. Contact Vercel Support: https://vercel.com/help
