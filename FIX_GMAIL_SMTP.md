# 🔐 Gmail SMTP Fix - App Password Required

## The Real Problem

Your Gmail password `Travel.NewUU.0207` is a regular password, but Gmail requires an **App Password** for SMTP access when 2FA is enabled.

---

## ✅ Solution: Enable 2FA and Generate App Password

### Step 1: Enable 2-Factor Authentication

1. **Go to:** https://myaccount.google.com/security
2. **Find:** "2-Step Verification"
3. **Click:** "Get Started"
4. **Follow the setup:**
   - Add your phone number
   - Verify with a code
   - Complete the setup
5. **Wait 5-10 minutes** after enabling 2FA

### Step 2: Generate App Password

1. **After 2FA is enabled, go to:**
   https://myaccount.google.com/apppasswords

2. **If you see the page:**
   - Select app: **Mail**
   - Select device: **Other (Custom name)**
   - Name: **Travel Bot**
   - Click **Generate**

3. **Copy the 16-character password:**
   - Example: `abcd efgh ijkl mnop`
   - Remove spaces: `abcdefghijklmnop`

4. **Update your `.env` file:**
   ```env
   EMAIL=travel@newuu.uz
   EMAIL_PASSWORD=abcdefghijklmnop
   ```

5. **Restart your application**

---

## 🧪 Test Locally First

Before deploying to Render, test locally:

```bash
cd /Users/burkhonnurmurodov/Documents/Travel\ Bot
source .venv/bin/activate

python << 'EOF'
import smtplib
from config import Config

try:
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
    server.starttls()
    server.login(Config.EMAIL, Config.EMAIL_PASSWORD)
    print("✅ SUCCESS! SMTP authentication works!")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Authentication failed: {e}")
    print("\nYou need to:")
    print("1. Enable 2FA on Gmail")
    print("2. Generate App Password")
    print("3. Use App Password (not regular password)")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

---

## 🚫 If App Passwords Not Available

You saw "The setting you are looking for is not available" because 2FA wasn't enabled.

### Must do FIRST:
1. ✅ Enable 2-Step Verification: https://myaccount.google.com/security
2. ⏰ Wait 5-10 minutes
3. ✅ Then try App Passwords: https://myaccount.google.com/apppasswords

---

## 🔄 Alternative: Use Outlook

If you can't enable 2FA on travel@newuu.uz (e.g., organization restrictions), use Outlook instead:

### Option A: Create New Outlook Account

1. **Create account:** https://outlook.live.com/
2. **Update `.env`:**
   ```env
   EMAIL=yourname@outlook.com
   EMAIL_PASSWORD=your_outlook_password
   ```

3. **Update `email_service.py` line 28:**
   ```python
   self.smtp_server = "smtp-mail.outlook.com"
   ```

4. **Test and deploy!**

---

## 📝 Step-by-Step for Gmail

### Current State:
```env
EMAIL=travel@newuu.uz
EMAIL_PASSWORD=Travel.NewUU.0207  ← Regular password (won't work!)
```

### What to do:

1. **Enable 2FA:**
   - Visit: https://myaccount.google.com/security
   - Enable "2-Step Verification"
   - Verify phone number

2. **Generate App Password:**
   - Visit: https://myaccount.google.com/apppasswords
   - Create password for "Mail" / "Travel Bot"
   - Copy 16-character password

3. **Update `.env`:**
   ```env
   EMAIL=travel@newuu.uz
   EMAIL_PASSWORD=abcdefghijklmnop  ← 16-char App Password
   ```

4. **Test locally:**
   ```bash
   python -c "import smtplib; s=smtplib.SMTP('smtp.gmail.com',587); s.starttls(); s.login('travel@newuu.uz', 'YOUR_APP_PASSWORD'); print('Works!'); s.quit()"
   ```

5. **Deploy to Render:**
   - Update `EMAIL_PASSWORD` environment variable on Render
   - Use the same 16-character App Password

---

## ⚠️ Common Mistakes

1. ❌ Using regular password instead of App Password
2. ❌ Not enabling 2FA first
3. ❌ Including spaces in App Password (`abcd efgh` → should be `abcdefgh`)
4. ❌ Not waiting after enabling 2FA
5. ❌ Using old/revoked App Password

---

## 🎯 Quick Decision Tree

```
Can you access travel@newuu.uz Google Account?
  ├─ YES → Can you enable 2FA?
  │    ├─ YES → Follow Gmail setup above ✅
  │    └─ NO  → Use Outlook instead ✅
  └─ NO → Use Outlook or ask admin for access
```

---

## 🚀 Recommended: Use Outlook (Easier)

If Gmail is too complicated, Outlook is simpler:

1. **No App Password needed**
2. **No 2FA required**
3. **Works immediately**

**Quick setup:**
```env
EMAIL=your-email@outlook.com
EMAIL_PASSWORD=your_regular_password
```

Update `email_service.py` line 28:
```python
self.smtp_server = "smtp-mail.outlook.com"
```

Done! ✅

---

## 📞 Need Help?

**If Gmail App Passwords still not showing:**
- Account may be managed by organization
- Contact IT/admin at newuu.uz
- They may need to enable App Passwords

**Best alternative:**
Create personal Outlook account for the bot.

---

💡 **Recommendation:** If travel@newuu.uz has restrictions, create a dedicated Outlook account like `putravelbot@outlook.com` for the bot. It's simpler and works everywhere!
