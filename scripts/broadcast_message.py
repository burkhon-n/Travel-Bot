"""
Broadcast a message to all registered users.
"""
import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import bot
from database import get_db
from models.User import User

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def send_broadcast():
    """Send broadcast message to all users."""
    
    print("🚀 Starting broadcast...")
    
    message = (
        "⚠️ <b>Attention</b> ⚠️\n\n"
        "Some users are stopping right after registering with Google — but that's not the end! "
        "To officially join the trip, please follow these steps:\n"
        "1️⃣ Send /trips command to see the list of available trips;\n"
        "2️⃣ Choose the trip you want to join;\n"
        "3️⃣ Read the agreement carefully and press \"I agree\";\n"
        "4️⃣ Send a screenshot of your payment receipt (at least half of the total) to reserve your seat.\n\n"
        "💙 After completing these steps, your seat will be confirmed!"
    )
    
    # Get all users from database
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        users = db.query(User).all()
        total_users = len(users)
        success_count = 0
        fail_count = 0
        
        logging.info(f"Found {total_users} users to send message to")
        
        for user in users:
            try:
                await bot.send_message(
                    user.telegram_id,
                    message,
                    parse_mode='HTML'
                )
                success_count += 1
                logging.info(f"✅ Sent to user {user.telegram_id} ({user.first_name} {user.last_name})")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.05)
                
            except Exception as e:
                fail_count += 1
                logging.error(f"❌ Failed to send to user {user.telegram_id}: {e}")
        
        logging.info(f"\n📊 Broadcast complete!")
        logging.info(f"Total users: {total_users}")
        logging.info(f"✅ Success: {success_count}")
        logging.info(f"❌ Failed: {fail_count}")
        
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


if __name__ == "__main__":
    asyncio.run(send_broadcast())
