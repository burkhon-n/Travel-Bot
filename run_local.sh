#!/bin/bash
# Local development server

echo "🚀 Starting Travel Bot (Local Development)"
echo "==========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create a .env file with the following variables:"
    echo "  BOT_TOKEN=your_bot_token"
    echo "  BOT_USERNAME=your_bot_username"
    echo "  URL=http://localhost:8000"
    echo "  CLIENT_ID=your_google_client_id"
    echo "  CLIENT_SECRET=your_google_client_secret"
    echo "  REDIRECT_URI=http://localhost:8000/auth/callback"
    echo "  DATABASE_URL=your_postgres_url"
    echo "  ADMINS=123456789,987654321"
    echo "  BYPASS_TELEGRAM_CHECK=true"
    echo ""
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found. Using system Python."
fi

echo ""
echo "🌐 Server will be available at:"
echo "   http://localhost:8000"
echo ""
echo "📱 Public pages:"
echo "   http://localhost:8000/home"
echo "   http://localhost:8000/privacy"
echo ""
echo "🔧 Admin (set BYPASS_TELEGRAM_CHECK=true in .env):"
echo "   http://localhost:8000/admin"
echo ""
echo "📚 API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==========================================="
echo ""

# Run uvicorn with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
