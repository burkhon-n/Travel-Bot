"""Project configuration.

Loads environment variables from a `.env` file located in the project root
and exposes a `Config` class with typed attributes and helpers.

Features:
- Supports DATABASE_URL override (useful for deployed environments).
- Builds a PostgreSQL URL from components and URL-encodes credentials.
- Safe parsing for integers and lists (DB_PORT, ADMINS).
- Explicit `.env` path loading to avoid surprises when running from other CWDs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List
from urllib.parse import quote_plus
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from dotenv import load_dotenv


# load .env from project root (file next to this script)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # Public settings
    URL: str = os.getenv("URL", "http://localhost:8000")

    # Full database URL override (e.g., from hosting providers)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "") or \
        os.getenv("POSTGRES_URL", "") or \
        os.getenv("POSTGRES_URL_NON_POOLING", "") or \
        os.getenv("POSTGRES_PRISMA_URL", "")

    # Database components (used if DATABASE_URL is not set)
    # Support common alternative env names used in different projects (.env)
    DB_HOST: str = os.getenv("DB_HOST", os.getenv("DB_HOSTNAME", os.getenv("POSTGRES_HOST", "localhost")))
    try:
        DB_PORT: int = int(os.getenv("DB_PORT", os.getenv("DB_DBPORT", "5432")) or 5432)
    except (TypeError, ValueError):
        DB_PORT = 5432

    # accept either DB_USER or DB_USERNAME
    DB_USER: str = os.getenv("DB_USER", os.getenv("DB_USERNAME", os.getenv("POSTGRES_USER", "user")))
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", os.getenv("DB_PASS", os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "password"))))
    # accept either DB_NAME or DB_DATABASE
    DB_NAME: str = os.getenv("DB_NAME", os.getenv("DB_DATABASE", os.getenv("POSTGRES_DATABASE", "database")))

    # optional DB_CONNECTION like 'pgsql' in some .env files — map to SQLAlchemy scheme
    DB_CONNECTION: str = os.getenv("DB_CONNECTION", os.getenv("DB_DRIVER", ""))

    # Bot settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")

    # ADMINS: comma-separated ints
    _ADMINS_RAW: str = os.getenv("ADMINS", "")
    ADMINS: List[int] = []
    if _ADMINS_RAW:
        for _part in _ADMINS_RAW.split(','):
            part = _part.strip()
            if not part:
                continue
            try:
                ADMINS.append(int(part))
            except ValueError:
                # ignore bad values
                continue

    CHANNEL: str = os.getenv("CHANNEL", "")
    CLIENT_ID: str = os.getenv("CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
    # Optional explicit OAuth redirect URI to ensure exact match with Google Console
    OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "")
    
    # Email settings for sending notifications
    EMAIL: str = os.getenv("EMAIL", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")

    @staticmethod
    def get_database_url() -> str:
        """Return a full database URL.

        Priority:
        1. `DATABASE_URL` env var (if present)
        2. Build a postgresql:// URL from DB_* components

        Username/password/db name are URL-encoded for safety.
        """
        if Config.DATABASE_URL:
            url = Config.DATABASE_URL.strip()
            # Strip surrounding quotes if present
            if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
                url = url[1:-1]
            # Normalize common provider URLs for SQLAlchemy
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)

            # Remove unsupported/unknown query parameters that psycopg2 rejects
            try:
                parts = urlsplit(url)
                if parts.query:
                    q = parse_qsl(parts.query, keep_blank_values=True)
                    allowed = {
                        'sslmode', 'ssl', 'sslrootcert', 'sslcert', 'sslkey',
                        'application_name', 'options', 'connect_timeout',
                        'keepalives', 'keepalives_idle', 'keepalives_interval', 'keepalives_count',
                        'target_session_attrs', 'gssencmode', 'krbsrvname', 'service',
                        'fallback_application_name', 'client_encoding', 'replication'
                    }
                    filtered = [(k, v) for (k, v) in q if k in allowed]
                    new_query = urlencode(filtered)
                    url = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
            except Exception:
                # If any error occurs, fall back to the normalized URL without changes
                pass
            return url

        user = quote_plus(str(Config.DB_USER))
        password = quote_plus(str(Config.DB_PASSWORD))
        host = Config.DB_HOST
        port = Config.DB_PORT
        dbname = quote_plus(str(Config.DB_NAME))

        # Determine scheme: allow DB_CONNECTION aliases (e.g., 'pgsql')
        scheme = "postgresql"
        if Config.DB_CONNECTION:
            conn = Config.DB_CONNECTION.lower()
            if conn in ("pgsql", "postgres", "postgresql"):
                scheme = "postgresql"
            elif conn in ("mysql", "mysql2"):
                scheme = "mysql"
            elif conn.startswith("sqlite"):
                scheme = "sqlite"

        if scheme == "sqlite":
            # For sqlite, DB_NAME is a file path; if empty use in-memory
            if not Config.DB_NAME or Config.DB_NAME in (":memory:", "memory"):
                return "sqlite:///:memory:"
            return f"sqlite:///{Config.DB_NAME}"

        return f"{scheme}://{user}:{password}@{host}:{port}/{dbname}"

    @staticmethod
    def get_oauth_redirect_uri() -> str:
        """Return the redirect URI for OAuth flows.

        Priority: explicit OAUTH_REDIRECT_URI env var, otherwise build from Config.URL
        and '/auth/callback'. This ensures the value can be set exactly to match the
        redirect URI registered in Google Console (avoids redirect_uri_mismatch).
        """
        if Config.OAUTH_REDIRECT_URI:
            return Config.OAUTH_REDIRECT_URI
        return f"{Config.URL.rstrip('/')}/auth/callback"
    
    @staticmethod
    def validate() -> List[str]:
        """Validate critical configuration and return list of errors/warnings.
        
        Returns:
            List of error/warning messages. Empty list means all is good.
        """
        errors = []
        
        # Critical settings
        if not Config.BOT_TOKEN:
            errors.append("❌ CRITICAL: BOT_TOKEN is not set")
        if not Config.BOT_USERNAME:
            errors.append("⚠️  WARNING: BOT_USERNAME is not set")
        if not Config.CLIENT_ID:
            errors.append("⚠️  WARNING: CLIENT_ID is not set (OAuth will not work)")
        if not Config.CLIENT_SECRET:
            errors.append("⚠️  WARNING: CLIENT_SECRET is not set (OAuth will not work)")
        if not Config.ADMINS:
            errors.append("⚠️  WARNING: No ADMINS configured (admin features disabled)")
        
        # Database validation
        try:
            db_url = Config.get_database_url()
            if not db_url or db_url == "sqlite:///:memory:":
                errors.append("⚠️  WARNING: Using in-memory database (data will be lost on restart)")
        except Exception as e:
            errors.append(f"❌ CRITICAL: Failed to build database URL: {e}")
        
        return errors


# Export a convenience instance for simple import in app code if desired
cfg = Config()
