"""
Configuration for Odesa Seaport Weather Forecast System.
"""

import os

# ============================================================
# LOCATION
# ============================================================
LATITUDE = 46.4857   # Odesa port coordinates
LONGITUDE = 30.7438
LOCATION_NAME = "Odesa Seaport"
LOCATION_NAME_RU = "Морський торговий порт Одеса"

# ============================================================
# PORT STORM THRESHOLDS (per Odesa Seaport Regulations)
# ============================================================
STORM_WIND_MPS = 14.0       # Vessel entry/exit PROHIBITED
RESTRICTED_WIND_MPS = 10.0  # Towing, gas carriers, disabled vessels
STORM_WAVE_M = 3.5          # Entry/exit prohibited
RESTRICTED_WAVE_M = 2.5     # Towing required

# ============================================================
# WEATHER API: Open-Meteo (free, no API key required)
# ============================================================
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

# ============================================================
# OUTPUT
# ============================================================
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# NOTIFICATION CHANNELS
# ============================================================

# --- Email ---
# Default recipient: Alexey Odesa
DEFAULT_RECIPIENT = "alexey.odessa85@gmail.com"

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))  # SSL port (recommended for Gmail)
SMTP_USER = os.getenv("SMTP_USER", "")          # sender Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")   # Gmail app password (NOT your Gmail password!)
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = [r.strip() for r in os.getenv("EMAIL_TO", DEFAULT_RECIPIENT).split(",") if r.strip()]

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")  # comma-separated

# --- Microsoft Teams / Slack Webhook ---
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# ============================================================
# SCHEDULE (cron-style)
# ============================================================
# Run every day at 06:00 (before morning shift)
CRON_SCHEDULE = "0 6 * * *"
