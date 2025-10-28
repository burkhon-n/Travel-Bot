"""
Add CASCADE delete to foreign keys in trip_members table.

This migration adds ON DELETE CASCADE to the user_id and trip_id foreign keys,
allowing automatic deletion of trip_members when a user or trip is deleted.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import engine
from sqlalchemy import text


def add_cascade_delete():
    """Add CASCADE delete to foreign keys."""
    
    with engine.connect() as conn:
        print("🔄 Adding CASCADE delete to foreign keys...")
        
        try:
            # Start transaction
            trans = conn.begin()
            
            # Drop existing foreign key constraints
            print("   Dropping old foreign key constraints...")
            conn.execute(text("""
                ALTER TABLE trip_members 
                DROP CONSTRAINT IF EXISTS trip_members_user_id_fkey
            """))
            
            conn.execute(text("""
                ALTER TABLE trip_members 
                DROP CONSTRAINT IF EXISTS trip_members_trip_id_fkey
            """))
            
            # Add new foreign keys with CASCADE
            print("   Adding new foreign keys with CASCADE...")
            conn.execute(text("""
                ALTER TABLE trip_members 
                ADD CONSTRAINT trip_members_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            """))
            
            conn.execute(text("""
                ALTER TABLE trip_members 
                ADD CONSTRAINT trip_members_trip_id_fkey 
                FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
            """))
            
            # Commit transaction
            trans.commit()
            
            print("✅ Successfully added CASCADE delete to foreign keys!")
            print("\nℹ️  Now when a user is deleted, all their trip_members records will be automatically deleted.")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add CASCADE Delete")
    print("=" * 60)
    
    response = input("\n⚠️  This will modify the database schema. Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        add_cascade_delete()
    else:
        print("\n❌ Migration cancelled.")
