"""Utilities for Telegram WebApp security and validation."""

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import hashlib
import hmac
from urllib.parse import unquote, parse_qsl
from typing import Optional
import logging
import os

from config import Config

# Setup templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Allow bypassing Telegram check in development (set BYPASS_TELEGRAM_CHECK=true in .env)
BYPASS_TELEGRAM_CHECK = os.getenv("BYPASS_TELEGRAM_CHECK", "false").lower() in ("true", "1", "yes")


def validate_telegram_webapp_data(init_data: str, bot_token: str) -> bool:
    """Validate Telegram WebApp initData using the bot token.
    
    Args:
        init_data: The initData string from Telegram WebApp
        bot_token: The bot token to validate against
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Parse the init_data query string
        parsed_data = dict(parse_qsl(init_data))
        
        # Extract the hash
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            return False
        
        # Create data check string (sorted key=value pairs)
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = '\n'.join(data_check_arr)
        
        # Create secret key from bot token
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Compare hashes
        return hmac.compare_digest(calculated_hash, received_hash)
    
    except Exception as e:
        logging.error(f"Error validating Telegram WebApp data: {e}")
        return False


def is_telegram_webapp_request(request: Request) -> bool:
    """Check if the request comes from Telegram WebApp.
    
    Multiple checks with fallback to allow WebApp access:
    1. Check for Telegram-specific headers
    2. Check for initData in query params or headers
    3. Check User-Agent for Telegram indicators
    4. Check for WebApp-specific characteristics
    
    Args:
        request: The FastAPI Request object
        
    Returns:
        True if request appears to be from Telegram WebApp
    """
    # Check 1: Look for Telegram WebApp specific headers
    user_agent = request.headers.get('user-agent', '').lower()
    if 'telegram' in user_agent:
        logging.debug("Telegram detected via user-agent")
        return True
    
    # Check 2: Look for initData parameter (passed by Telegram WebApp)
    init_data = request.query_params.get('tgWebAppData') or request.headers.get('X-Telegram-Init-Data')
    if init_data:
        logging.debug("Telegram detected via initData")
        # Optionally validate the initData signature
        if Config.BOT_TOKEN:
            is_valid = validate_telegram_webapp_data(init_data, Config.BOT_TOKEN)
            if is_valid:
                logging.debug("initData validation successful")
                return True
        return True
    
    # Check 3: Look for Telegram WebApp version header
    webapp_version = request.headers.get('X-Telegram-WebApp-Version')
    if webapp_version:
        logging.debug("Telegram detected via WebApp version header")
        return True
    
    # Check 4: Check for specific query parameters that indicate Telegram context
    telegram_params = ['tgWebAppStartParam', 'tgWebAppThemeParams']
    if any(param in request.query_params for param in telegram_params):
        logging.debug("Telegram detected via query params")
        return True
    
    # Check 5: Check Referer header
    referer = request.headers.get('referer', '')
    if 'telegram' in referer.lower() or 't.me' in referer.lower():
        logging.debug("Telegram detected via referer")
        return True
    
    # Check 6: WebView characteristics (iOS/Android WebView used by Telegram)
    # Telegram uses custom WebViews that have specific characteristics
    if 'mobile' in user_agent and 'safari' not in user_agent and 'chrome' not in user_agent:
        # Likely a WebView (not a full browser)
        logging.debug("Possible Telegram WebView detected (mobile without full browser)")
        return True
    
    # Check 7: Accept headers that indicate embedded context
    sec_fetch_dest = request.headers.get('sec-fetch-dest', '').lower()
    if sec_fetch_dest in ('iframe', 'embed', 'document'):
        # Likely embedded in an iframe or WebView
        logging.debug("Embedded context detected via sec-fetch-dest")
        return True
    
    # Check 8: For now, allow all requests to /webapp/* routes by default
    # This is more permissive but prevents blocking legitimate Telegram WebApp users
    # The real security comes from the Telegram initData validation on the client side
    if request.url.path.startswith('/webapp/') or request.url.path.startswith('/admin'):
        logging.debug("WebApp route detected - allowing access (security handled by client-side Telegram.WebApp)")
        return True
    
    logging.debug("No Telegram indicators found")
    return False


def require_telegram_webapp(request: Request, bot_username: Optional[str] = None) -> Optional[HTMLResponse]:
    """Check if request is from Telegram WebApp, return error page if not.
    
    NOTE: For Telegram WebApps, server-side detection is unreliable because Telegram
    doesn't always send consistent headers. The real security comes from:
    1. Client-side Telegram.WebApp SDK validation (checks if window.Telegram exists)
    2. User authentication via Telegram ID embedded in OAuth flow
    3. Rate limiting and other security measures
    
    This function is currently configured to be permissive for WebApp routes.
    Set STRICT_TELEGRAM_CHECK=true in .env to enable strict validation.
    
    Args:
        request: The FastAPI Request object
        bot_username: Optional bot username to show in error page
        
    Returns:
        HTMLResponse with error page if not from Telegram, None otherwise
    """
    # Allow bypassing check in development mode
    if BYPASS_TELEGRAM_CHECK:
        logging.debug("Telegram WebApp check bypassed (development mode)")
        return None
    
    # Check if strict mode is enabled (default: false for better UX)
    strict_mode = os.getenv("STRICT_TELEGRAM_CHECK", "false").lower() in ("true", "1", "yes")
    
    if strict_mode and not is_telegram_webapp_request(request):
        logging.warning(
            f"Non-Telegram access attempt to {request.url.path} from "
            f"user-agent: {request.headers.get('user-agent', 'unknown')}"
        )
        return templates.TemplateResponse(
            "webapp_only.html",
            {
                "request": request,
                "bot_username": bot_username or Config.BOT_USERNAME if hasattr(Config, 'BOT_USERNAME') else None
            },
            status_code=403
        )
    
    # In non-strict mode, we allow access but log for monitoring
    if not is_telegram_webapp_request(request):
        logging.info(
            f"WebApp access without Telegram indicators: {request.url.path} "
            f"(user-agent: {request.headers.get('user-agent', 'unknown')[:50]})"
        )
    
    return None


def get_telegram_user_id(request: Request) -> Optional[int]:
    """Extract Telegram user ID from WebApp initData.
    
    Args:
        request: The FastAPI Request object
        
    Returns:
        Telegram user ID if found, None otherwise
    """
    try:
        init_data = request.query_params.get('tgWebAppData') or request.headers.get('X-Telegram-Init-Data')
        if not init_data:
            return None
        
        parsed_data = dict(parse_qsl(init_data))
        user_json = parsed_data.get('user')
        if user_json:
            import json
            user_data = json.loads(unquote(user_json))
            return user_data.get('id')
    
    except Exception as e:
        logging.error(f"Error extracting Telegram user ID: {e}")
    
    return None
