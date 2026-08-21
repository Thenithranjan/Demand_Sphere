"""
Supabase Client — Singleton
============================
Initialises the ``supabase-py`` client once at import time.

All modules that need Supabase Storage, Auth, or Realtime should
import ``supabase`` from here rather than creating their own clients.

Usage:
    from app.supabase_client import supabase

    # Upload a file to storage
    supabase.storage.from_("reports").upload("path/file.json", data)

    # Download a file
    supabase.storage.from_("reports").download("path/file.json")

Environment variables required:
    SUPABASE_URL  — your project URL (e.g. https://xxxx.supabase.co)
    SUPABASE_KEY  — your service role key (NOT the anon key)
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("app.supabase_client")

# ---------------------------------------------------------------------------
# Load .env if not already loaded
# ---------------------------------------------------------------------------
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip("'\"")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip("'\"")

# ---------------------------------------------------------------------------
# Initialise the Supabase client (singleton)
# ---------------------------------------------------------------------------
supabase = None  # type: ignore[assignment]

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client, Client  # type: ignore[import]
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info(f"[supabase_client] Connected to Supabase project: {SUPABASE_URL}")
    except Exception as exc:
        logger.error(
            f"[supabase_client] Failed to initialise Supabase client: {exc}. "
            "Storage features will be unavailable."
        )
else:
    logger.warning(
        "[supabase_client] SUPABASE_URL or SUPABASE_KEY not set — "
        "Supabase Storage will be unavailable. Set them in backend/.env to enable."
    )
