from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
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
# Disable public API docs endpoints for security (/docs, /redoc, /openapi.json)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Setup Jinja2 templates for public pages
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# include routers so endpoints are available
app.include_router(webhook_router)
app.include_router(auth_router)
app.include_router(webapp_router)
app.include_router(trips_router)
app.include_router(admin_router)


async def initialize_bot():
	"""Initialize database tables, webhook, and bot commands."""
	results = {
		"database": "not_attempted",
		"webhook": "not_attempted",
		"commands": "not_attempted",
		"config_errors": []
	}
	
	# Validate configuration
	config_errors = Config.validate()
	if config_errors:
		results["config_errors"] = config_errors
		for error in config_errors:
			logging.warning(error)
	
	# create database tables (guarded) — if DB is unreachable or misconfigured,
	# log and continue so the FastAPI app can still start for debugging.
	try:
		Base.metadata.create_all(bind=engine)
		logging.info("✅ Database tables created/verified successfully")
		results["database"] = "success"
	except OperationalError as e:
		logging.exception(
			"Database error during create_all; tables not created. Verify your DB settings in .env and that the DB server is running. Error: %s",
			e,
		)
		results["database"] = f"error: {str(e)}"
		return results

	# attempt to set webhook so Telegram sends updates to our FastAPI endpoint
	if Config.BOT_TOKEN and Config.URL:
		url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/setWebhook"
		payload = {"url": f"{Config.URL}/webhook/{Config.BOT_TOKEN}"}
		try:
			resp = requests.post(url, json=payload, timeout=10)
			logging.info("Set webhook response: %s", resp.text)
			results["webhook"] = "success"
		except Exception as e:
			logging.exception("Failed to set webhook on startup")
			results["webhook"] = f"error: {str(e)}"

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
			results["commands"] = "success"
		except Exception as e:
			logging.exception("Failed to set bot commands on startup")
			results["commands"] = f"error: {str(e)}"
	else:
		results["webhook"] = "skipped: BOT_TOKEN or URL not configured"
		results["commands"] = "skipped: BOT_TOKEN or URL not configured"
	
	return results


@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
	"""Serve the public home page.
	
	Publicly accessible page providing information about Travel Bot.
	Required for Google Cloud Console app publication.
	"""
	logging.info("public.home render")
	return templates.TemplateResponse("home.html", {"request": request})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
	"""Serve the privacy policy page.
	
	Publicly accessible page detailing privacy practices.
	Required for Google Cloud Console app publication.
	"""
	logging.info("public.privacy render")
	return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/")
async def root():
	"""Root endpoint - Initialize bot and return status."""
	init_results = await initialize_bot()
	
	return {
		"name": "Travel Bot API",
		"version": "1.3.0",
		"description": "Telegram bot for managing group travel trips with payment tracking",
		"initialization": init_results,
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
			"trips": "/trips"
		}
	}


@app.on_event('startup')
async def startup():
	"""Run initialization on application startup."""
	await initialize_bot()
