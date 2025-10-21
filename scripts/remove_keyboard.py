import asyncio
import logging
import os
import sys
from telebot import types

# Ensure project root is on sys.path so `from bot import bot` works
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Reuse existing bot setup
from bot import bot

CHAT_ID = -1003105687230  # default; can be overridden via CLI

async def main(chat_id: int):
    try:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        # Create a reply keyboard remove markup
        markup = types.ReplyKeyboardRemove(selective=False)
        text = "✅ Keyboard removed. Use /menu to open inline options."
        await bot.send_message(chat_id, text, reply_markup=markup)
        print("✅ Sent keyboard removal message to:", chat_id)
    except Exception as e:
        print("❌ Failed to send keyboard removal message:", e)

if __name__ == "__main__":
    chat = CHAT_ID
    if len(sys.argv) > 1:
        try:
            chat = int(sys.argv[1])
        except Exception:
            print("⚠️ Invalid chat id provided; using default.")
    asyncio.run(main(chat))
