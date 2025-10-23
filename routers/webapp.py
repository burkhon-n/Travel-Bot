"""Telegram Web App routes for registration and other interactive flows."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import requests

from config import Config
from database import get_db
from models.User import User
from sqlalchemy.orm import Session
import logging
from webapp_security import require_telegram_webapp

router = APIRouter(prefix="/webapp", tags=["webapp"])

# Setup Jinja2 templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    """Serve the public home page.
    
    This page is publicly accessible and provides information about Travel Bot.
    Required for Google Cloud Console app publication.
    """
    logging.info("webapp.home render")
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """Serve the privacy policy page.
    
    This page is publicly accessible and details our privacy practices.
    Required for Google Cloud Console app publication.
    """
    logging.info("webapp.privacy render")
    return templates.TemplateResponse("privacy.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_webapp(request: Request):
    """Serve the Telegram Web App registration page.
    
    This page uses Telegram.WebApp SDK to get the user's Telegram ID,
    then redirects to Google OAuth with that ID in the state parameter.
    
    Only accessible from Telegram WebApp for security.
    """
    # Check if request is from Telegram WebApp
    error_response = require_telegram_webapp(request, Config.BOT_USERNAME)
    if error_response:
        return error_response
    
    logging.info("webapp.register render")
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "client_id": Config.CLIENT_ID,
            "redirect_uri": Config.get_oauth_redirect_uri(),
        }
    )


@router.get("/create-trip", response_class=HTMLResponse)
async def create_trip_webapp(request: Request):
    """Serve the Telegram Web App for creating a new trip.
    
    This page allows bot admins to create and configure a new trip
    for a group that just added the bot.
    
    Only accessible from Telegram WebApp for security.
    """
    # Check if request is from Telegram WebApp
    error_response = require_telegram_webapp(request, Config.BOT_USERNAME)
    if error_response:
        return error_response
    
    group_id = request.query_params.get("group_id")
    group_name = request.query_params.get("group_name", "Unknown Group")
    
    if not group_id:
        raise HTTPException(status_code=400, detail="group_id is required")
    
    logging.info("webapp.create_trip render group_id=%s group_name=%s", group_id, group_name)
    return templates.TemplateResponse(
        "create_trip_minimal.html",
        {
            "request": request,
            "group_id": group_id,
            "group_name": group_name,
        }
    )


@router.get("/trip-stats", response_class=HTMLResponse)
async def trip_stats_webapp(request: Request):
    """Render a statistics page for a given trip.
    Shows counts for half-paid, full-paid, total registered, and seats available.
    
    Only accessible from Telegram WebApp for security.
    """
    # Check if request is from Telegram WebApp
    error_response = require_telegram_webapp(request, Config.BOT_USERNAME)
    if error_response:
        return error_response
    
    params = request.query_params
    trip_id = params.get("trip_id")
    if not trip_id:
        raise HTTPException(status_code=400, detail="trip_id is required")
    try:
        trip_id_int = int(trip_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="trip_id must be an integer")

    from models.Trip import Trip
    from models.TripMember import TripMember, PaymentStatus

    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id_int).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        total_registered = db.query(TripMember).filter(TripMember.trip_id == trip.id).count()
        half_paid = db.query(TripMember).filter(
            TripMember.trip_id == trip.id,
            TripMember.payment_status == PaymentStatus.half_paid
        ).count()
        full_paid = db.query(TripMember).filter(
            TripMember.trip_id == trip.id,
            TripMember.payment_status == PaymentStatus.full_paid
        ).count()
        # Half-paid and full-paid both reserve seats
        paid_count = half_paid + full_paid

        participant_limit = trip.participant_limit
        if participant_limit is None:
            seats_available = None
            occupancy_pct = None
        else:
            seats_available = max(participant_limit - paid_count, 0)
            occupancy_pct = int(min(paid_count / participant_limit * 100, 100)) if participant_limit > 0 else 0

        logging.info(
            "webapp.trip_stats render trip_id=%s total=%s half=%s full=%s paid=%s limit=%s",
            trip.id, total_registered, half_paid, full_paid, paid_count, participant_limit,
        )
        return templates.TemplateResponse(
            "trip_stats.html",
            {
                "request": request,
                "trip": trip,
                "trip_name": trip.name,
                "price": trip.price,
                "total_registered": total_registered,
                "half_paid": half_paid,
                "full_paid": full_paid,
                "paid_count": paid_count,
                "participant_limit": participant_limit,
                "seats_available": seats_available,
                "occupancy_pct": occupancy_pct,
            }
        )
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@router.get("/agenda", response_class=HTMLResponse)
async def trip_agenda_webapp(request: Request):
    """Render trip agenda/schedule page.
    
    Shows the detailed itinerary for the trip.
    Accessible from Telegram WebApp.
    """
    # Check if request is from Telegram WebApp
    error_response = require_telegram_webapp(request, Config.BOT_USERNAME)
    if error_response:
        return error_response
    
    params = request.query_params
    trip_id = params.get("trip_id")
    
    # For now, we'll use the Samarkand trip agenda
    # In the future, you can add logic to select different agendas based on trip_id
    
    logging.info("webapp.agenda render trip_id=%s", trip_id)
    return templates.TemplateResponse(
        "agenda/smarkand_trip.html",
        {
            "request": request,
        }
    )
