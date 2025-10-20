"""Migration script to add price column to trips table."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from database import engine, SessionLocal
from models.Trip import Trip

def migrate():
    """Add price column to trips table."""
    db = SessionLocal()
    
    try:
        print("🔄 Starting migration: Add price column to trips table...")
        
        # Check if price column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='trips' AND column_name='price'
        """))
        
        if result.fetchone():
            print("✅ Price column already exists. No migration needed.")
            return
        
        # Add price column with default value of 0
        print("➕ Adding price column to trips table...")
        db.execute(text("""
            ALTER TABLE trips 
            ADD COLUMN price INTEGER NOT NULL DEFAULT 0
        """))
        db.commit()
        
        print("✅ Price column added successfully!")
        
        # Update existing trips to have a default price
        existing_trips = db.query(Trip).filter(Trip.price == 0).all()
        
        if existing_trips:
            print(f"\n⚠️  Found {len(existing_trips)} existing trips with price = 0")
            print("Please update these trips manually with actual prices:")
            for trip in existing_trips:
                print(f"   - Trip ID {trip.id}: {trip.name}")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
