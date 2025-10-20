from fastapi import APIRouter, Request, HTTPException
from config import Config
from bot import bot, types
import requests
import logging

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("/", include_in_schema=False)
async def set_webhook():
    """Set webhook endpoint - hidden from docs for security."""
    url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/setWebhook"
    payload = {"url": f"{Config.URL}/webhook/{Config.BOT_TOKEN}"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        logging.info("webhook.set response=%s", response.text)
        return response.json()
    except Exception as e:
        logging.exception("webhook.set failed")
        return {"ok": False, "error": str(e)}

@router.post('/{token}', include_in_schema=False)
async def receive_webhook(request: Request, token: str):
    """Receive webhook from Telegram - hidden from docs for security."""
    # Verify the token matches to prevent unauthorized access
    if token != Config.BOT_TOKEN:
        logging.warning("webhook.unauthorized_attempt token=%s", token[:10] + "...")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    data = await request.json()
    logging.info("webhook.update received keys=%s", list(data.keys()))
    update = types.Update.de_json(data)
    await bot.process_new_updates([update])
    return {"ok": True}