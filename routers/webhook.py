from fastapi import APIRouter, Request
from config import Config
from bot import bot, types
import requests
import logging

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("/")
async def set_webhook():
    url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/setWebhook"
    payload = {"url": f"{Config.URL}/webhook/{Config.BOT_TOKEN}"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        logging.info("webhook.set response=%s", response.text)
        return response.json()
    except Exception as e:
        logging.exception("webhook.set failed")
        return {"ok": False, "error": str(e)}

@router.post(f'/{Config.BOT_TOKEN}')
async def receive_webhook(request: Request):
    data = await request.json()
    logging.info("webhook.update received keys=%s", list(data.keys()))
    update = types.Update.de_json(data)
    await bot.process_new_updates([update])
    return {"ok": True}