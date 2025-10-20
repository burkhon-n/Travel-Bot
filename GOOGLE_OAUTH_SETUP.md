# Google OAuth Setup Instructions

## Error: "Failed to exchange code: 400 Client Error: Bad Request"

This error occurs because the redirect URI is not authorized in Google Cloud Console.

## Fix: Add Redirect URI to Google Cloud Console

### Step 1: Open Google Cloud Console
Go to: https://console.cloud.google.com/

### Step 2: Navigate to Credentials
1. Select your project
2. Go to **APIs & Services** → **Credentials**
3. Find your OAuth 2.0 Client ID (the one matching your `CLIENT_ID` in `.env`)
4. Click the **Edit** button (pencil icon)

### Step 3: Add Authorized Redirect URI
In the **Authorized redirect URIs** section, add:

```
https://bf501ba21f65.ngrok-free.app/auth/callback
```

**Important Notes:**
- ✅ Must match exactly (including https://)
- ✅ No trailing slash
- ✅ Must match `OAUTH_REDIRECT_URI` in your `.env` file
- ⚠️ If your ngrok URL changes, update both:
  - `.env` file (`URL` and `OAUTH_REDIRECT_URI`)
  - Google Cloud Console (Authorized redirect URIs)

### Step 4: Save Changes
Click **SAVE** at the bottom of the page.

### Step 5: Wait (if needed)
Changes may take a few minutes to propagate, but usually work immediately.

### Step 6: Test
Try the registration flow again from your Telegram bot.

---

## Current Configuration

From your `.env` file:
- **URL**: `https://bf501ba21f65.ngrok-free.app`
- **OAUTH_REDIRECT_URI**: `https://bf501ba21f65.ngrok-free.app/auth/callback`
- **CLIENT_ID**: `802523640333-8tr2hnni3cbjr7ge81klhpcjjv770175.apps.googleusercontent.com`

These values must match what's in Google Cloud Console!

---

## Testing Checklist

After adding the redirect URI, test:
1. ✅ Open bot in Telegram
2. ✅ Send `/start`
3. ✅ Click "Register with Google"
4. ✅ Should open browser (not show error)
5. ✅ Sign in with @newuu.uz email
6. ✅ Should redirect back to success page
7. ✅ Check bot for confirmation message

---

## Common Issues

### Issue: "redirect_uri_mismatch"
**Solution**: The URI in Google Console doesn't exactly match. Check for:
- Trailing slashes
- http vs https
- Port numbers
- Spelling

### Issue: "disallowed_useragent"
**Solution**: Already fixed! OAuth now opens in external browser.

### Issue: ngrok URL keeps changing
**Solution**: Use ngrok with a static domain (requires paid plan) or update both `.env` and Google Console each time ngrok restarts.

---

## Quick Reference: Google Cloud Console

**Direct link to credentials:**
https://console.cloud.google.com/apis/credentials

**What to look for:**
- OAuth 2.0 Client IDs section
- Your client ID ending in `...googleusercontent.com`
- Authorized redirect URIs list
