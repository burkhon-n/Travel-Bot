# 📁 Project Structure - Travel Bot

Complete overview of all files and directories in the Travel Bot project.

## 🗂️ Directory Structure

```
Travel Bot/
├── 📄 README.md                      # Main project documentation
├── 📄 DEPLOYMENT.md                   # Production deployment guide
├── 📄 GOOGLE_OAUTH_SETUP.md          # OAuth configuration guide
├── 📄 WEBAPP_SECURITY.md             # WebApp security documentation
├── 📄 ERROR_CODES.md                 # Error codes reference
├── 📄 .gitignore                     # Git ignore configuration
├── 📄 requirements.txt               # Python dependencies
│
├── 🐍 Core Application Files
│   ├── main.py                       # FastAPI application entry point
│   ├── bot.py                        # Telegram bot handlers
│   ├── config.py                     # Configuration management
│   ├── database.py                   # Database connection & session
│   └── webapp_security.py            # WebApp validation utilities
│
├── 📊 models/                        # Database models (SQLAlchemy)
│   ├── __init__.py                   # Package initialization
│   ├── User.py                       # User model
│   ├── Trip.py                       # Trip model
│   └── TripMember.py                 # TripMember model (with indexes)
│
├── 🛣️ routers/                       # FastAPI route handlers
│   ├── auth.py                       # Google OAuth callback
│   ├── admin.py                      # Admin dashboard & API
│   ├── webapp.py                     # WebApp pages
│   ├── webhook.py                    # Telegram webhook handler
│   └── trips.py                      # Trip management API
│
├── 🎨 templates/                     # Jinja2 HTML templates
│   ├── register.html                 # User registration page
│   ├── success.html                  # Post-registration success
│   ├── error.html                    # Error display page
│   ├── admin_dashboard.html          # Admin trip list
│   ├── admin_trip.html               # Trip detail management
│   ├── create_trip_minimal.html      # Trip creation form
│   ├── trip_stats.html               # Live trip statistics
│   └── webapp_only.html              # Base WebApp template
│
├── 🔧 utils/                         # Utility modules
│   └── logging_config.py             # Logging configuration
│
└── 📜 scripts/                       # Maintenance scripts
    ├── reset_db.py                   # Database initialization
    └── cleanup_unused_files.py       # File cleanup utility
```

## 📄 File Descriptions

### Core Application

#### `main.py`
**Purpose**: FastAPI application entry point  
**Key Features**:
- Router registration (auth, admin, webapp, webhook, trips)
- Webhook configuration on startup
- Bot command menu setup
- Configuration validation
- Lifespan events (startup/shutdown)

**Critical Functions**:
- `lifespan()` - Application lifecycle management
- `set_bot_commands()` - Registers Telegram commands
- `set_webhook()` - Configures Telegram webhook

#### `bot.py`
**Purpose**: All Telegram bot message handlers and callbacks  
**Key Features**:
- Comprehensive error handling with `format_error_message()`
- User registration flow
- Trip discovery and registration
- Receipt upload and payment tracking
- Admin payment approval/rejection
- Status checking and help commands

**Critical Functions**:
- `format_error_message()` - Utility for consistent error formatting
- `handle_message()` - Main message router
- `handle_start()` - Registration flow
- `handle_group_member()` - Paid member verification
- `handle_receipt()` - Payment receipt processing with race condition protection

#### `config.py`
**Purpose**: Environment variable management and validation  
**Key Features**:
- Loads all configuration from `.env`
- Database URL construction with fallbacks
- OAuth redirect URI generation
- Configuration validation on startup

**Critical Methods**:
- `get_database_url()` - Builds PostgreSQL connection URL
- `get_oauth_redirect_uri()` - Constructs OAuth callback URL
- `validate()` - Validates critical settings

#### `database.py`
**Purpose**: Database connection and session management  
**Key Features**:
- SQLAlchemy engine setup
- Connection pooling configuration
- Session factory
- Async context manager for sessions

#### `webapp_security.py`
**Purpose**: Telegram WebApp data validation  
**Key Features**:
- HMAC signature verification
- initData parsing and validation
- User data extraction

### Models

#### `models/User.py`
**Purpose**: User account model  
**Fields**:
- `telegram_id` (unique) - Telegram user ID
- `first_name`, `last_name` - User name
- `email` - Verified @newuu.uz email
- `created_at` - Registration timestamp

#### `models/Trip.py`
**Purpose**: Trip/event model  
**Fields**:
- `name` - Trip name
- `group_id` (unique) - Telegram group ID
- `participant_limit` - Max participants (nullable)
- `price` - Trip price in UZS (required)
- `card_info` - Payment card details
- `agreement_text` - Terms and conditions
- `participant_invite_link` - Direct join link
- `guest_invite_link` - Join request link
- `status` - active/completed/cancelled

#### `models/TripMember.py`
**Purpose**: Trip membership and payment tracking  
**Fields**:
- `user_id` - Foreign key to User
- `trip_id` - Foreign key to Trip
- `payment_status` - not_paid/half_paid/full_paid (enum)
- `payment_receipt_file_id` - Telegram file ID
- `joined_at` - Registration timestamp

**Indexes**:
- Composite index on (trip_id, payment_status)
- Composite index on (user_id, payment_status)
- Composite index on (user_id, joined_at)

**Constraints**:
- Unique constraint on (user_id, trip_id)

### Routers

#### `routers/auth.py`
**Purpose**: Google OAuth callback handler  
**Endpoints**:
- `GET /auth/callback` - OAuth callback, user upsert, redirect

**Features**:
- Email domain validation (@newuu.uz)
- User data upsert
- Welcome message dispatch
- Error pages for OAuth failures

#### `routers/admin.py`
**Purpose**: Admin dashboard and API  
**Endpoints**:
- `GET /admin` - Dashboard with trip list
- `GET /admin/trip/{trip_id}` - Trip detail page
- `POST /api/member/{member_id}/status` - Update payment status
- `POST /api/member/{member_id}/kick` - Remove member
- `POST /api/invite-links/{trip_id}/regenerate` - Regenerate invite links

**Features**:
- Admin authorization via Telegram ID
- User full name and ID display
- Real-time member management
- Payment status updates with notifications

#### `routers/webapp.py`
**Purpose**: WebApp page serving  
**Endpoints**:
- `GET /register` - Registration page
- `GET /create-trip` - Trip creation form
- `GET /trip-stats` - Trip statistics viewer

**Features**:
- Telegram WebApp initData validation
- User context extraction
- Dynamic content rendering

#### `routers/webhook.py`
**Purpose**: Telegram webhook endpoint  
**Endpoints**:
- `POST /webhook` - Receives Telegram updates

**Features**:
- Async update processing
- Error handling and logging
- Integration with bot handlers

#### `routers/trips.py`
**Purpose**: Trip management API  
**Endpoints**:
- `POST /api/trips` - Create new trip

**Features**:
- Trip creation with validation
- Group link generation
- WebApp initData validation

### Templates

#### `templates/register.html`
**Purpose**: OAuth registration page  
**Features**:
- Google OAuth button
- External browser opening via `tg.openLink()`
- WebApp auto-close after button press
- Telegram styling

#### `templates/success.html`
**Purpose**: Post-registration success page  
**Features**:
- Success message display
- Auto-redirect to bot (opens @putravelbot)
- 2-second delay before redirect

#### `templates/error.html`
**Purpose**: Generic error display  
**Features**:
- Error message rendering
- Error code display
- Actionable suggestions
- Return to bot button

#### `templates/admin_dashboard.html`
**Purpose**: Admin trip list dashboard  
**Features**:
- Trip cards with statistics
- Participant counts
- Trip management links
- Create trip button

#### `templates/admin_trip.html`
**Purpose**: Trip detail and member management  
**Features**:
- Member list with full names and Telegram IDs
- Payment status buttons (Not/Half/Full)
- Kick member functionality
- Invite link regeneration
- Telegram confirmations via `tg.showConfirm()`

#### `templates/create_trip_minimal.html`
**Purpose**: Trip creation form  
**Features**:
- Input fields for all trip details
- Form validation
- Submit to `/api/trips`
- WebApp integration

#### `templates/trip_stats.html`
**Purpose**: Live trip statistics  
**Features**:
- Real-time participant counts
- Paid vs unpaid breakdown
- Capacity information
- Auto-refresh capability

### Utilities

#### `utils/logging_config.py`
**Purpose**: Centralized logging configuration  
**Features**:
- Log format standardization
- Log level configuration
- File/console output setup

### Scripts

#### `scripts/reset_db.py`
**Purpose**: Database initialization and reset  
**Features**:
- Drops all tables
- Creates fresh schema
- Useful for development/testing

**⚠️ Warning**: Deletes all data!

#### `scripts/cleanup_unused_files.py`
**Purpose**: Reference cleanup script  
**Features**:
- Identifies unused files
- Safe cleanup operations
- Kept for documentation purposes

## 🔒 Security Files

### `.gitignore`
**Purpose**: Prevents sensitive files from being committed  
**Protected Items**:
- `.env` (environment variables)
- `__pycache__/` (Python cache)
- `*.pyc` (compiled Python)
- Virtual environments (`.venv/`, `venv/`, `env/`)
- OS files (`.DS_Store`)
- IDE files (`.vscode/`, `.idea/`)

## 📦 Dependencies (`requirements.txt`)

**Core Dependencies**:
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `pyTelegramBotAPI` - Telegram bot library
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL adapter
- `python-dotenv` - Environment variable loader
- `jinja2` - Template engine
- `python-multipart` - Form data parsing
- `requests` - HTTP client
- `httpx` - Async HTTP client

## 📚 Documentation Files

### `README.md`
**Purpose**: Main project documentation  
**Sections**:
- Features overview
- Installation guide
- Bot commands
- User flow
- Configuration
- Troubleshooting

### `DEPLOYMENT.md`
**Purpose**: Production deployment guide  
**Sections**:
- VPS deployment (Ubuntu)
- Heroku deployment
- Docker deployment
- SSL setup
- Monitoring
- Backup strategy

### `GOOGLE_OAUTH_SETUP.md`
**Purpose**: OAuth configuration guide  
**Sections**:
- Google Cloud Console setup
- Redirect URI configuration
- Domain restriction
- Troubleshooting OAuth errors

### `WEBAPP_SECURITY.md`
**Purpose**: WebApp security documentation  
**Sections**:
- initData validation
- HMAC signature verification
- Security best practices

### `ERROR_CODES.md`
**Purpose**: Error codes reference  
**Sections**:
- Error code categories (1000s-9000s)
- Error descriptions and solutions
- Debugging tips
- Error recovery procedures

## 🚫 Removed Files

These files were removed during project finalization:
- ❌ `cleanup_templates.py` - Temporary template fix script
- ❌ `fix_templates.py` - Temporary template fix script
- ❌ All `__pycache__/` directories - Python cache
- ❌ All `*.pyc` files - Compiled Python bytecode

## 📊 File Statistics

- **Total Files**: ~30 essential files
- **Python Files**: 15 (.py files)
- **Templates**: 8 (.html files)
- **Documentation**: 5 (.md files)
- **Configuration**: 2 (.env, .gitignore)
- **Lines of Code**: ~3,500+ (Python)

## 🔄 File Dependencies

```
main.py
├── config.py
├── database.py
├── bot.py
├── routers/
│   ├── auth.py → models/User
│   ├── admin.py → models/Trip, TripMember
│   ├── webapp.py → webapp_security.py
│   ├── webhook.py → bot.py
│   └── trips.py → models/Trip
└── models/
    ├── User.py → database.py
    ├── Trip.py → database.py
    └── TripMember.py → database.py, User, Trip
```

## 🎯 Quick File Lookup

### Need to...
- **Add a bot command** → `bot.py`
- **Add an API endpoint** → `routers/*.py`
- **Change database schema** → `models/*.py`
- **Update OAuth flow** → `routers/auth.py`, `templates/register.html`
- **Modify admin dashboard** → `templates/admin_dashboard.html`, `routers/admin.py`
- **Add configuration** → `config.py`, `.env`
- **Fix error messages** → `bot.py` (format_error_message)
- **Update deployment** → `DEPLOYMENT.md`

---

**Last Updated**: January 2025  
**Project Status**: Production Ready ✅
