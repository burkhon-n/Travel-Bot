# 🚀 SendGrid Setup for Production (Render)

## Problem

Render (and many hosting platforms) block outbound SMTP connections for security.
You're seeing: `OSError: [Errno 101] Network is unreachable`

## Solution: Use SendGrid

SendGrid uses HTTP API instead of SMTP ports, so it works on all platforms.

---

## 📝 Setup Steps (5 minutes)

### 1. Create SendGrid Account

1. Go to: https://signup.sendgrid.com/
2. Sign up (free tier: 100 emails/day)
3. Verify your email address

### 2. Create API Key

1. Log into SendGrid
2. Go to: **Settings → API Keys**
   - Or direct link: https://app.sendgrid.com/settings/api_keys
3. Click **"Create API Key"**
4. **Name:** `Travel Bot`
5. **Permissions:** Select "Full Access" (or "Mail Send" minimum)
6. Click **"Create & View"**
7. **Copy the API key** (starts with `SG.`)
   - ⚠️ You can only see this once! Save it now.

### 3. Add to Render Environment Variables

1. Go to your Render Dashboard
2. Select your service
3. Go to **"Environment"** tab
4. Click **"Add Environment Variable"**
5. **Key:** `SENDGRID_API_KEY`
6. **Value:** `SG.your_api_key_here` (paste the key you copied)
7. Click **"Save Changes"**

### 4. Deploy

Render will automatically redeploy with the new environment variable.

---

## ✅ Verification

After deployment, check your logs:

```
Email service initialized with SendGrid
```

Instead of:

```
Email service initialized with SMTP (smtp.gmail.com)
```

---

## 🧪 Local Testing

If you want to test SendGrid locally:

1. Add to your `.env` file:
   ```env
   SENDGRID_API_KEY=SG.your_api_key_here
   ```

2. Test:
   ```bash
   python -c "from email_service import get_email_service; s = get_email_service(); print(f'Using: {\"SendGrid\" if s.use_sendgrid else \"SMTP\"}')"
   ```

---

## 🔄 How It Works

The email service now **automatically detects** which method to use:

### On Render (Production):
```
✅ SENDGRID_API_KEY is set
→ Uses SendGrid API
→ Works perfectly!
```

### Locally (Development):
```
❌ SENDGRID_API_KEY not set
→ Uses SMTP (Gmail)
→ Works for local testing
```

---

## 📊 SendGrid Features

**Free Tier:**
- ✅ 100 emails per day (forever free)
- ✅ Email validation
- ✅ Delivery analytics
- ✅ No credit card required

**Paid Plans:**
- $19.95/month for 50,000 emails
- Better deliverability
- Advanced analytics
- Dedicated IP

---

## 🎯 SendGrid Dashboard

After sending emails, check:

**Activity Feed:**
https://app.sendgrid.com/email_activity

See:
- Emails sent
- Delivered
- Opened (if tracking enabled)
- Failed deliveries

---

## ⚙️ Code Changes Made

### 1. Updated `email_service.py`:
- ✅ Added SendGrid support
- ✅ Auto-detects SendGrid vs SMTP
- ✅ Falls back to SMTP if SendGrid not available

### 2. Updated `requirements.txt`:
- ✅ Added `sendgrid` package

### 3. Updated `.env` and `.env.example`:
- ✅ Added `SENDGRID_API_KEY` configuration

---

## 🐛 Troubleshooting

### "SendGrid API error"

**Check:**
1. API key is correct (starts with `SG.`)
2. API key has "Mail Send" permission
3. SendGrid account is verified
4. Environment variable is set in Render

### "Using SMTP" on Render

**Fix:**
1. Make sure you added `SENDGRID_API_KEY` to Render Environment
2. Redeploy after adding the variable
3. Check logs for "Email service initialized with SendGrid"

### Still seeing network errors

**Verify:**
1. `sendgrid` is in `requirements.txt` ✅
2. Render redeployed after changes
3. Environment variable key is exactly: `SENDGRID_API_KEY`

---

## 📧 Sender Verification (Optional)

For better deliverability, verify your sender email:

1. Go to: https://app.sendgrid.com/settings/sender_auth
2. **Single Sender Verification:**
   - Add: travel@newuu.uz
   - Verify via email link
3. Or **Domain Authentication** (advanced):
   - Authenticate entire @newuu.uz domain
   - Better for high volume

---

## 💰 Cost Comparison

| Service | Free Tier | Cost |
|---------|-----------|------|
| Gmail SMTP | ⚠️ Blocked on Render | Free |
| SendGrid | ✅ 100/day | Free |
| Mailgun | 5,000/month | Free |
| AWS SES | 62,000/month | Free (first year) |

**Recommendation:** Start with SendGrid free tier (100/day is plenty for most use cases)

---

## 🚀 Quick Start

**TL;DR:**
1. Sign up: https://signup.sendgrid.com/
2. Get API key: https://app.sendgrid.com/settings/api_keys
3. Add to Render: `SENDGRID_API_KEY=SG.your_key`
4. Deploy
5. Done! ✅

No code changes needed - the email service auto-detects SendGrid!

---

## 📞 Support

- SendGrid Docs: https://docs.sendgrid.com/
- SendGrid Support: https://support.sendgrid.com/
- Dashboard: https://app.sendgrid.com/

---

💙 Once configured, congratulations emails will work perfectly on Render!
