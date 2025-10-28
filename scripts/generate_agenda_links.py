"""
Generate shareable Telegram Mini App links for trip agendas.

This script generates shareable links that open the trip agenda
directly in Telegram as a Mini App.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db
from models.Trip import Trip, TripStatus
from config import Config


def generate_agenda_links():
    """Generate shareable agenda links for all active trips."""
    
    # Get bot username from config
    bot_username = getattr(Config, 'BOT_USERNAME', None)
    if not bot_username:
        print("❌ BOT_USERNAME not set in Config!")
        print("\nPlease add BOT_USERNAME to your config.py:")
        print("BOT_USERNAME = 'your_bot_username'  # without @")
        return
    
    # Remove @ if present
    bot_username = bot_username.lstrip('@')
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Get all active trips
        active_trips = db.query(Trip).filter(Trip.status == TripStatus.active).all()
        
        if not active_trips:
            print("📭 No active trips found.")
            return
        
        print(f"📅 Agenda Links for Active Trips\n")
        print("=" * 60)
        
        for trip in active_trips:
            # Web App URL (for internal use)
            webapp_url = f"{Config.URL.rstrip('/')}/webapp/agenda?trip_id={trip.id}"
            
            # Telegram Mini App Link (shareable - opens directly in Telegram)
            # Format: https://t.me/BOT_USERNAME/APP_SHORT_NAME?startapp=PARAMS
            mini_app_link = f"https://t.me/{bot_username}/agenda?startapp=trip_{trip.id}"
            
            # Alternative: Deep Link (requires bot /start handler)
            deep_link = f"https://t.me/{bot_username}?start=agenda_{trip.id}"
            
            print(f"\n🎫 {trip.name}")
            print(f"   ID: {trip.id}")
            print(f"\n   📱 Direct Mini App Link (RECOMMENDED):")
            print(f"   {mini_app_link}")
            print(f"\n   🔗 Alternative Deep Link:")
            print(f"   {deep_link}")
            print(f"\n   � WebApp URL (backend):")
            print(f"   {webapp_url}")
            print("-" * 60)
        
        print(f"\n✅ Generated {len(active_trips)} agenda link(s)")
        
        print("\n" + "=" * 60)
        print("📖 How to use these links:")
        print("=" * 60)
        print("\n🎯 MINI APP LINK (Recommended):")
        print("   • Opens agenda directly in Telegram WebApp")
        print("   • No extra button clicks needed")
        print("   • Perfect for sharing in channels, messages, etc.")
        print("\n🔄 DEEP LINK (Alternative):")
        print("   • Opens bot first, then shows agenda button")
        print("   • Good for onboarding new users")
        print("   • Works with /start command handler")
        print("\n✅ Your Mini App is registered at: t.me/putravelbot/agenda")
        
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


if __name__ == "__main__":
    generate_agenda_links()
