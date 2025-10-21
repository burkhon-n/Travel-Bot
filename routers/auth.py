from fastapi import APIRouter, Request, HTTPException
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import requests
import logging
import asyncio

from config import Config
from database import get_db
from models.User import User
from utils.text_utils import format_name

router = APIRouter(prefix="", tags=["auth"])

# Setup Jinja2 templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    """Handle Google OAuth callback.

    Expects `code` and `state` query params. `state` should contain the Telegram id.
    Exchanges the code for tokens, validates the id_token via Google's tokeninfo
    endpoint, ensures the email belongs to `newuu.uz`, then creates/updates a User.
    """
    params = dict(request.query_params)
    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = Config.get_oauth_redirect_uri()
    payload = {
        "code": code,
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        token_resp = requests.post(token_url, data=payload, timeout=10)
        token_resp.raise_for_status()
        tokens = token_resp.json()
    except requests.exceptions.HTTPError as e:
        logging.exception("auth.exchange failed")
        # Return user-friendly error page
        error_detail = "Unknown error"
        try:
            error_data = e.response.json() if e.response else {}
            error_detail = error_data.get("error_description", error_data.get("error", str(e)))
        except:
            error_detail = str(e)
        
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Google OAuth Configuration Error",
                "error_details": (
                    f"Failed to complete sign-in: {error_detail}\n\n"
                    f"⚙️ Admin Action Required:\n"
                    f"Add this redirect URI to Google Cloud Console:\n"
                    f"👉 {redirect_uri}\n\n"
                    f"Go to: Google Cloud Console → APIs & Services → Credentials → "
                    f"OAuth 2.0 Client IDs → Edit → Authorized redirect URIs"
                ),
                "error_code": "OAUTH_EXCHANGE_FAILED"
            },
            status_code=502
        )
    except Exception as e:
        logging.exception("auth.exchange failed")
        raise HTTPException(status_code=502, detail=f"Failed to exchange code: {e}")

    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(status_code=502, detail="No id_token returned by token endpoint")

    # Validate id_token using Google's tokeninfo endpoint
    try:
        info_resp = requests.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token}, timeout=10)
        info_resp.raise_for_status()
        info = info_resp.json()
    except Exception as e:
        logging.exception("auth.tokeninfo failed")
        raise HTTPException(status_code=502, detail=f"Failed to validate id_token: {e}")

    email = info.get("email")
    email_verified = info.get("email_verified") in ("true", True)
    hosted_domain = info.get("hd")

    # Enforce newuu.uz domain
    if not email or not email_verified or not (email.endswith("@newuu.uz") or hosted_domain == "newuu.uz"):
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Invalid Email Domain",
                "error_details": "You must use a student Google account ending with @newuu.uz to register.",
                "error_code": "DOMAIN_MISMATCH"
            },
            status_code=400
        )

    # Use state as telegram id
    try:
        tg_id = int(state)
    except Exception:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Invalid Request",
                "error_details": "The registration state is invalid. Please start the registration process again from the bot.",
                "error_code": "INVALID_STATE"
            },
            status_code=400
        )

    # Create or update user in DB
    db_gen = get_db()
    db = next(db_gen)
    try:
        logging.info("auth.user upsert tg_id=%s email=%s", tg_id, email)
        
        # Get and format names from Google
        raw_first_name = info.get("given_name", "")
        raw_last_name = info.get("family_name", "")
        
        # Format names with proper capitalization
        formatted_first_name = format_name(raw_first_name) if raw_first_name else None
        formatted_last_name = format_name(raw_last_name) if raw_last_name else None
        
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if user:
            user.email = email
            user.first_name = formatted_first_name or user.first_name
            user.last_name = formatted_last_name or user.last_name
        else:
            user = User(
                telegram_id=tg_id,
                first_name=formatted_first_name,
                last_name=formatted_last_name,
                email=email
            )
            db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send onboarding instructions to user via bot
        from bot import bot
        
        def send_onboarding_sync():
            """Send onboarding messages to newly registered user."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Success notification
                    loop.run_until_complete(
                        bot.send_message(
                            tg_id,
                            "🎉 <b>Registration Successful!</b>\n\n"
                            "Welcome to Travel Bot! You're all set to start exploring trips.",
                            parse_mode='HTML'
                        )
                    )

                    # Detailed usage instructions
                    help_text = (
                        "📖 <b>Quick Start Guide</b>\n\n"
                        "<b>Available Commands:</b>\n"
                        "🎫 <b>/trips</b> – Browse and register for trips\n"
                        "💳 <b>/mystatus</b> – Check your payment status\n"
                        "📊 <b>/stats</b> – View trip statistics\n"
                        "🧭 <b>/menu</b> – Main menu with all options\n"
                        "❓ <b>/help</b> – Full usage guide\n\n"
                        "<b>How it works:</b>\n"
                        "1️⃣ Find a trip with /trips\n"
                        "2️⃣ Register and confirm the agreement\n"
                        "3️⃣ Upload a 50% payment receipt\n"
                        "4️⃣ Upload final payment receipt to complete\n"
                        "5️⃣ Get your confirmed seat!\n\n"
                        "💡 <i>Tip: Use /menu anytime to see available actions.</i>"
                    )
                    loop.run_until_complete(
                        bot.send_message(tg_id, help_text, parse_mode='HTML')
                    )
                finally:
                    loop.close()
            except Exception as e:
                logging.error(f"Error sending onboarding messages to user {tg_id}: {e}", exc_info=True)
        
        # Send onboarding synchronously before returning response
        try:
            send_onboarding_sync()
        except Exception as e:
            logging.error(f"Failed to queue onboarding for user {tg_id}: {e}")
            pass
        
        # Build user display name
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or email.split('@')[0]
        
        # Return styled success page
        return templates.TemplateResponse(
            "success.html",
            {
                "request": request,
                "email": email,
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "telegram_id": tg_id,
                "user_name": user_name,
                "bot_username": Config.BOT_USERNAME.lstrip('@')  # Remove @ if present
            }
        )
    except Exception as e:
        db.rollback()
        logging.exception("auth.user upsert failed tg_id=%s", tg_id)
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Database Error",
                "error_details": "Failed to save your account. Please try again later.",
                "error_code": f"DB_ERROR: {str(e)[:100]}"
            },
            status_code=500
        )
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
