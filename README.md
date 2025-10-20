# 🌍 Travel Bot - Group Trip Management System

A comprehensive Telegram bot for managing group trips with integrated payment tracking, seat reservations, and participant management.

## 📋 Features

### For Users
- **Google OAuth Registration** - Secure sign-in with @newuu.uz student accounts
- **Trip Discovery** - Browse available trips with real-time statistics
- **Easy Registration** - Simple process to join trips
- **Payment Tracking** - Upload receipts and track payment status (50% / Full)
- **Seat Reservation** - Automatic seat reservation upon payment
- **Live Statistics** - View trip capacity and participant status
- **Status Tracking** - Check registration and payment status anytime

### For Admins
- **Admin Dashboard** - Web-based interface for trip management
- **Trip Creation** - Set up new trips with payment info and agreements
- **Member Management** - View participants, update payment status, kick members
- **Payment Review** - Approve/reject payment receipts
- **Invite Link Management** - Separate links for participants and guests
- **Real-time Updates** - Live participant counts and statistics

### Technical Features
- **Race Condition Protection** - Prevents overbooking when multiple users upload receipts
- **Database Indexing** - Optimized queries for performance
- **Error Handling** - User-friendly error messages with actionable steps
- **Transaction Safety** - Automatic rollbacks on errors
- **Duplicate Prevention** - Unique constraints prevent double registrations

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL database (Supabase or local)
- Telegram Bot Token
- Google OAuth 2.0 credentials (@newuu.uz domain)
- ngrok or similar for local development

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Travel Bot"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Bot Configuration
   BOT_TOKEN=your_telegram_bot_token
   BOT_USERNAME=your_bot_username
   URL=https://your-ngrok-url.ngrok-free.app
   
   # Database (Supabase or local PostgreSQL)
   DATABASE_URL=postgresql://user:password@host:port/database
   # OR use individual components:
   # DB_HOST=localhost
   # DB_PORT=5432
   # DB_USER=postgres
   # DB_PASSWORD=yourpassword
   # DB_NAME=travel_bot
   
   # Google OAuth
   CLIENT_ID=your_google_client_id
   CLIENT_SECRET=your_google_client_secret
   OAUTH_REDIRECT_URI=https://your-ngrok-url.ngrok-free.app/auth/callback
   
   # Admin Telegram IDs (comma-separated)
   ADMINS=123456789,987654321
   ```

5. **Set up Google OAuth**
   
   See [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) for detailed instructions.

6. **Initialize the database**
   ```bash
   python scripts/reset_db.py  # Creates all tables
   ```

7. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Expose with ngrok (for local development)**
   ```bash
   ngrok http 8000
   ```
   Update the `URL` in `.env` with your ngrok URL.

## 📱 Bot Commands

### User Commands
- `/start` - Register or return to main menu
- `/trips` - Browse available trips
- `/mystatus` - Check your registration status
- `/stats` - View trip statistics
- `/menu` - Quick navigation menu
- `/help` - User guide

### Admin Commands
- `/admin` - Open admin dashboard

## 🏗️ Project Structure

```
Travel Bot/
├── bot.py                 # Telegram bot handlers
├── main.py               # FastAPI application entry point
├── config.py             # Configuration management
├── database.py           # Database setup and session management
├── webapp_security.py    # Security utilities for WebApp
│
├── models/               # SQLAlchemy models
│   ├── User.py          # User model
│   ├── Trip.py          # Trip model
│   └── TripMember.py    # TripMember model with payment status
│
├── routers/             # FastAPI routers
│   ├── auth.py         # Google OAuth callback
│   ├── admin.py        # Admin dashboard and API
│   ├── webapp.py       # WebApp pages (register, create trip, stats)
│   ├── webhook.py      # Telegram webhook handler
│   └── trips.py        # Trip management API
│
├── templates/           # Jinja2 HTML templates
│   ├── register.html   # OAuth registration page
│   ├── success.html    # Registration success page
│   ├── error.html      # Error page
│   ├── admin_dashboard.html
│   ├── admin_trip.html
│   ├── create_trip_form.html
│   └── trip_stats.html
│
├── scripts/            # Utility scripts
│   └── reset_db.py    # Database initialization
│
└── utils/
    └── logging_config.py  # Logging configuration
```

## 🔄 User Flow

### Registration Flow
1. User sends `/start` to bot
2. Bot presents "Register with Google" WebApp button
3. User authenticates with @newuu.uz Google account
4. OAuth callback validates and creates user record
5. User redirected back to bot with success message

### Trip Registration Flow
1. User browses trips with `/trips`
2. Selects a trip, reviews terms and payment info
3. Confirms registration
4. Receives payment instructions
5. Uploads payment receipt (photo/PDF)
6. **Automatically marked as "50% Paid" - Seat Reserved**
7. Admin reviews receipt
8. Admin confirms or rejects payment
   - **Confirm**: User stays as 50% paid, gets group invite link
   - **Reject**: Status changed back to "Not Paid", seat released

### Payment Status Flow
```
Not Paid → (Upload Receipt) → 50% Paid (Seat Reserved) → (Admin Confirms) → 50% Paid (Confirmed)
                                     ↓
                            (Admin Rejects) → Not Paid (Seat Released)
```

## 🔐 Security Features

- **Telegram WebApp Validation** - Validates initData from Telegram
- **Admin Authorization** - Telegram ID-based admin access
- **OAuth Domain Restriction** - Only @newuu.uz accounts allowed
- **Database Transactions** - Atomic operations with rollback on error
- **Unique Constraints** - Prevents duplicate registrations
- **Race Condition Protection** - Prevents overbooking

## 📊 Database Schema

### Users
- `id` - Primary key
- `telegram_id` - Unique Telegram user ID
- `first_name`, `last_name` - User name
- `email` - Verified @newuu.uz email

### Trips
- `id` - Primary key
- `name` - Trip name
- `group_id` - Telegram group ID (unique)
- `participant_limit` - Max participants (nullable)
- `price` - Trip price in UZS (required)
- `card_info` - Payment card details
- `agreement_text` - Terms and conditions
- `participant_invite_link` - Direct join link for paid members
- `guest_invite_link` - Join request link for guests
- `status` - active/completed/cancelled

### TripMembers
- `id` - Primary key
- `user_id` - Foreign key to Users
- `trip_id` - Foreign key to Trips
- `payment_status` - not_paid/half_paid/full_paid
- `payment_receipt_file_id` - Telegram file ID
- `joined_at` - Registration timestamp
- **Unique constraint**: (user_id, trip_id)

## 🛠️ Maintenance Scripts

### Reset Database
Drops and recreates all tables:
```bash
python scripts/reset_db.py
```

**⚠️ Warning**: This deletes all data!

## 📝 Configuration Notes

### Bot Token
1. Create bot with [@BotFather](https://t.me/BotFather)
2. Get token and set in `.env`

### Google OAuth
1. Create project in [Google Cloud Console](https://console.cloud.google.com/)
2. Configure OAuth consent screen (Internal for @newuu.uz)
3. Create OAuth 2.0 Client ID credentials
4. Add redirect URI: `https://your-url/auth/callback`
5. Set CLIENT_ID and CLIENT_SECRET in `.env`

### Admin Setup
1. Get your Telegram user ID (use [@userinfobot](https://t.me/userinfobot))
2. Add to `ADMINS` in `.env` (comma-separated for multiple)

## 🐛 Troubleshooting

### "disallowed_useragent" error
- OAuth opens in external browser automatically
- Ensure OAUTH_REDIRECT_URI matches Google Console

### Database connection errors
- Check DATABASE_URL format
- Verify database server is running
- Check credentials and network access

### Bot not responding
- Verify BOT_TOKEN is correct
- Check webhook is set: `curl https://api.telegram.org/bot<token>/getWebhookInfo`
- Review application logs

### Race condition testing
- Multiple users can now safely upload receipts simultaneously
- System prevents overbooking with post-commit validation

## 📚 Documentation

- [Google OAuth Setup Guide](GOOGLE_OAUTH_SETUP.md)
- [WebApp Security](WEBAPP_SECURITY.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Add your license here]

## 👥 Support

For issues or questions:
- Check the troubleshooting section
- Review error messages (they include helpful context)
- Contact the development team

---

**Built with ❤️ for group travel management**
