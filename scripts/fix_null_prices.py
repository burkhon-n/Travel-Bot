#!/usr/bin/env python3
"""
Fix NULL prices in existing trips.
Sets price to 0 for trips that have NULL price.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal, engine
from models.Trip import Trip
from sqlalchemy import text

def fix_null_prices():
    """Update all trips with NULL price to 0."""
    session = SessionLocal()
    
    try:
        print("🔍 Checking for trips with NULL price...")
        
        # Check for NULL prices
        trips_with_null = session.query(Trip).filter(Trip.price == None).all()
        
        if not trips_with_null:
            print("✅ No trips with NULL price found. All good!")
            return
        
        print(f"⚠️  Found {len(trips_with_null)} trips with NULL price:")
        for trip in trips_with_null:
            print(f"   - ID: {trip.id}, Name: {trip.name}, Price: {trip.price}")
        
        # Fix NULL prices
        print("\n🔧 Updating NULL prices to 0...")
        count = session.query(Trip).filter(Trip.price == None).update({Trip.price: 0})
        session.commit()
        
        print(f"✅ Updated {count} trips")
        
        # Verify
        remaining = session.query(Trip).filter(Trip.price == None).count()
        if remaining > 0:
            print(f"⚠️  Warning: {remaining} trips still have NULL price")
        else:
            print("✅ All trips now have valid prices")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Fix NULL Prices Migration")
    print("=" * 60)
    print()
    
    fix_null_prices()
    
    print()
    print("=" * 60)
    print("✅ Migration complete!")
    print("=" * 60)
