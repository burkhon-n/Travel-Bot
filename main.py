from fastapi import FastAPI
from models import User, TripMember, Trip
from database import Base, engine
from config import Config
from bot import bot
from routers.webhook import router as webhook_router
from routers.auth import router as auth_router
from routers.webapp import router as webapp_router
from routers.trips import router as trips_router
from routers.admin import router as admin_router
import requests
import logging
from sqlalchemy.exc import OperationalError
import json
from utils.logging_config import setup_logging


setup_logging()
app = FastAPI()

# include routers so endpoints are available
app.include_router(webhook_router)
app.include_router(auth_router)
app.include_router(webapp_router)
app.include_router(trips_router)
app.include_router(admin_router)


@app.get("/")
async def root():
	"""Root endpoint - API information."""
	return {
		"name": "Travel Bot API",
		"version": "1.3.0",
		"description": "Telegram bot for managing group travel trips with payment tracking",
		"features": [
			"Trip management with pricing",
			"Google OAuth authentication",
			"Payment receipt uploads",
			"Admin dashboard",
			"Excel export for trip members",
			"Real-time statistics"
		],
		"endpoints": {
			"webhook": "/webhook/{token}",
			"auth": "/auth/google",
			"admin": "/admin/dashboard",
			"trips": "/trips",
			"docs": "/docs"
		},
		"documentation": "/docs"
	}


@app.on_event('startup')
async def startup():
	"""Create DB tables and register the Telegram webhook (if configured)."""
	# Validate configuration
	config_errors = Config.validate()
	if config_errors:
		for error in config_errors:
			logging.warning(error)
	
	# create database tables (guarded) — if DB is unreachable or misconfigured,
	# log and continue so the FastAPI app can still start for debugging.
	try:
		Base.metadata.create_all(bind=engine)
		logging.info("✅ Database tables created/verified successfully")
	except OperationalError as e:
		logging.exception(
			"Database error during create_all; tables not created. Verify your DB settings in .env and that the DB server is running. Error: %s",
			e,
		)
		# don't re-raise so the app doesn't crash on startup; user can fix DB separately
		return

	# attempt to set webhook so Telegram sends updates to our FastAPI endpoint
	if Config.BOT_TOKEN and Config.URL:
		url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/setWebhook"
		payload = {"url": f"{Config.URL}/webhook/{Config.BOT_TOKEN}"}
		try:
			resp = requests.post(url, json=payload, timeout=10)
			logging.info("Set webhook response: %s", resp.text)
		except Exception:
			logging.exception("Failed to set webhook on startup")

		# Set bot command menu for better UX
		try:
			commands = [
				{"command": "start", "description": "Start and register"},
				{"command": "menu", "description": "Open main menu"},
				{"command": "trips", "description": "Browse trips"},
				{"command": "stats", "description": "View live stats"},
				{"command": "mystatus", "description": "My registration/payment"},
				{"command": "help", "description": "How to use the bot"},
				{"command": "admin", "description": "Open admin tools"},
			]
			cmd_url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/setMyCommands"
			resp2 = requests.post(cmd_url, json={"commands": commands}, timeout=10)
			logging.info("Set commands response: %s", resp2.text)
		except Exception:
			logging.exception("Failed to set bot commands on startup")


@app.on_event('shutdown')
async def shutdown():
	"""Cleanup: try to remove webhook on shutdown."""
	if Config.BOT_TOKEN:
		url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/deleteWebhook"
		try:
			resp = requests.post(url, timeout=5)
			logging.info("Deleted webhook response: %s", resp.text)
		except Exception:
			logging.exception("Failed to delete webhook on shutdown")
