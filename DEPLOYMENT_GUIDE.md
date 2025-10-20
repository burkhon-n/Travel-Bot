# Deployment & Access Guide

## Public Pages (Browser Accessible)

These pages are accessible from any browser without Telegram:

- **Home Page**: `https://your-domain.vercel.app/home`
  - Showcases features and information about Travel Bot
  - Required for Google Cloud Console publication

- **Privacy Policy**: `https://your-domain.vercel.app/privacy`
  - Details privacy practices and data handling
  - Required for Google Cloud Console publication

## Protected Pages (Telegram Only)

These pages require access through Telegram WebApp and will show an error page when accessed from a browser:

### Admin Pages
- `/admin` - Admin dashboard (list of all trips)
- `/admin/trip/{trip_id}` - Trip detail page with member management

### User Pages
- `/webapp/register` - User registration with Google OAuth
- `/webapp/create-trip` - Create new trip (admin only)
- `/webapp/trip-stats` - View trip statistics

## Error Page Behavior

When you try to access a protected page from a regular browser, you will see:
- 🔒 "Telegram Required" error page
- Instructions on how to access through Telegram
- Link to download Telegram
- Explanation of security measures

## Environment Variables for Vercel

Make sure these are set in your Vercel project settings:

### Required
- `BOT_TOKEN` - Your Telegram bot token
- `BOT_USERNAME` - Your bot's username (e.g., @YourBot)
- `URL` - Your Vercel deployment URL (e.g., https://your-app.vercel.app)
- `CLIENT_ID` - Google OAuth client ID
- `CLIENT_SECRET` - Google OAuth client secret
- `REDIRECT_URI` - OAuth redirect URI (should be `https://your-domain.vercel.app/auth/callback`)
- `DATABASE_URL` - PostgreSQL connection string (Supabase)
- `ADMINS` - Comma-separated list of admin Telegram user IDs

### Optional Security Settings
- `STRICT_TELEGRAM_CHECK=true` (default) - Enforce Telegram-only access for protected pages
- `BYPASS_TELEGRAM_CHECK=false` (default) - Do NOT bypass Telegram checks in production

## Local Development

For local testing, add to your `.env` file:
```env
BYPASS_TELEGRAM_CHECK=true
```

This allows you to access protected pages from your browser during development.

## Testing Access

### Test Public Pages (should work in browser):
```bash
curl https://your-domain.vercel.app/home
curl https://your-domain.vercel.app/privacy
```

### Test Protected Pages (should show error page in browser):
```bash
curl https://your-domain.vercel.app/admin
# Should return HTML with "Telegram Required" message
```

### Test from Telegram WebApp:
1. Open your bot in Telegram
2. Send `/admin` command
3. Click the admin button
4. Should open the admin dashboard successfully

## Google Cloud Console URLs

When publishing your OAuth app, use these URLs:

- **Application Home Page**: `https://your-domain.vercel.app/home`
- **Privacy Policy URL**: `https://your-domain.vercel.app/privacy`
- **Terms of Service URL**: `https://your-domain.vercel.app/privacy` (or create separate terms page)
- **Authorized Redirect URIs**: 
  - `https://your-domain.vercel.app/auth/callback`

## Security Features

✅ **Enabled by Default:**
- Telegram WebApp validation for protected pages
- OAuth 2.0 authentication via Google
- Admin-only access controls
- Payment receipt verification
- HTTPS/TLS encryption

✅ **Public Access (No Auth Required):**
- Home page (`/home`)
- Privacy policy (`/privacy`)
- API documentation (`/docs`) - Shows only public endpoints

🔒 **Protected Access (Telegram WebApp Required):**
- All admin functions
- User registration
- Trip creation
- Trip statistics
- Payment management

## Troubleshooting

### "Telegram Required" showing when accessing from Telegram:
1. Make sure you're opening the page through the bot's buttons/commands
2. Check that `STRICT_TELEGRAM_CHECK` is set to `true` in Vercel
3. Verify the bot is properly configured with your Vercel URL

### Public pages not loading:
1. Check that Vercel deployment is successful
2. Verify DNS settings
3. Check Vercel logs for errors

### Admin page not working:
1. Verify your Telegram user ID is in the `ADMINS` environment variable
2. Make sure you're accessing through Telegram WebApp
3. Check the browser console for errors
