"""
Notification sender: Email, Telegram, and Webhook.
Auto-loads .env file from project root.
"""

import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

# Auto-load .env if present
_PROJECT_DIR = Path(__file__).resolve().parent
_ENV_FILE = _PROJECT_DIR / ".env"
if _ENV_FILE.exists():
    with open(_ENV_FILE) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)

from config.settings import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    EMAIL_FROM, EMAIL_TO,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS,
    WEBHOOK_URL
)


def send_email(subject, body_text, attachment_path=None, to_addrs=None):
    """Send forecast via email with optional chart attachment."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[Email] Skipped: SMTP credentials not configured")
        return False

    if to_addrs is None:
        to_addrs = [a.strip() for a in EMAIL_TO if a.strip()]
    if not to_addrs:
        print("[Email] Skipped: no recipients configured")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM or SMTP_USER
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        if attachment_path and Path(attachment_path).exists():
            part = MIMEBase("application", "octet-stream")
            with open(attachment_path, "rb") as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = Path(attachment_path).name
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            msg.attach(part)

        with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=30) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM or SMTP_USER, to_addrs, msg.as_string())

        print(f"[Email] Sent to {', '.join(to_addrs)}")
        return True
    except Exception as e:
        print(f"[Email] Error: {e}")
        return False


def send_telegram(message, photo_path=None):
    """Send forecast via Telegram bot (text + optional photo)."""
    if not TELEGRAM_BOT_TOKEN:
        print("[Telegram] Skipped: bot token not configured")
        return False

    chat_ids = [c.strip() for c in TELEGRAM_CHAT_IDS if c.strip()]
    if not chat_ids:
        print("[Telegram] Skipped: no chat IDs configured")
        return False

    results = []
    for chat_id in chat_ids:
        try:
            if photo_path and Path(photo_path).exists():
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                with open(photo_path, "rb") as photo:
                    resp = requests.post(
                        url,
                        data={"chat_id": chat_id, "caption": message[:1024]},
                        files={"photo": photo},
                        timeout=60
                    )
            else:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                resp = requests.post(
                    url,
                    json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                    timeout=60
                )

            if resp.ok:
                print(f"[Telegram] Sent to chat {chat_id}")
                results.append(True)
            else:
                print(f"[Telegram] Failed for {chat_id}: {resp.text}")
                results.append(False)
        except Exception as e:
            print(f"[Telegram] Error for {chat_id}: {e}")
            results.append(False)

    return any(results)


def send_webhook(payload):
    """Send JSON payload to webhook (Teams/Slack/etc)."""
    if not WEBHOOK_URL:
        print("[Webhook] Skipped: URL not configured")
        return False

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        if resp.ok:
            print("[Webhook] Sent successfully")
            return True
        else:
            print(f"[Webhook] Failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"[Webhook] Error: {e}")
        return False


def _format_email_body(report):
    """Format email body in the standard report layout."""
    date_str = report.get("date_str", "")
    r = report
    temps = r.get("temps", [])
    feels = r.get("feels_like", [])
    wind = r.get("wind_speed", [])
    wind_dir = r.get("wind_dir", [])
    precip = r.get("precip", [])
    humidity = r.get("humidity", [])
    pressure = r.get("pressure", [])
    status = r.get("port_status", "SAFE")
    alerts = r.get("alerts_en", [])

    max_temp = max(temps) if temps else 0
    min_temp = min(temps) if temps else 0
    max_feel = max(feels) if feels else 0
    min_feel = min(feels) if feels else 0
    max_wind = max(wind) if wind else 0
    min_wind = min(wind) if wind else 0
    dominant_wind = max(set(wind_dir), key=wind_dir.count) if wind_dir else "N"
    total_precip = sum(precip) if precip else 0
    max_hum = max(humidity) if humidity else 0
    min_hum = min(humidity) if humidity else 0
    min_press = min(pressure) if pressure else 0
    max_press = max(pressure) if pressure else 0

    # Wind description
    if max_wind < 3.4:
        wind_desc = "Light breeze"
    elif max_wind < 5.5:
        wind_desc = "Gentle breeze"
    elif max_wind < 8.0:
        wind_desc = "Moderate breeze"
    else:
        wind_desc = "Fresh breeze"

    # Pressure trend
    if pressure and pressure[-1] > pressure[0]:
        press_trend = "rising"
    elif pressure and pressure[-1] < pressure[0]:
        press_trend = "falling"
    else:
        press_trend = "stable"

    # Status block
    if status == "safe":
        status_block = (
            "⚓ PORT STATUS: SAFE\n\n"
            "No port operation restrictions.\n"
            f"Wind well below restricted (10 m/s) and storm (14 m/s) thresholds."
        )
    elif status == "restricted":
        status_block = (
            "⚓ PORT STATUS: RESTRICTED\n\n"
            "Towing required for vessel movements.\n"
            "Gas/chemical carriers and disabled vessels prohibited."
        )
    else:
        status_block = (
            "⚓ PORT STATUS: STORM\n\n"
            "Vessel entry/exit PROHIBITED.\n"
            "All port operations suspended."
        )

    if alerts:
        status_block += "\n\n" + "\n".join(f"⚠ {a}" for a in alerts)

    body = f"""🌤 Odesa Seaport Weather Forecast
{date_str}

TEMPERATURE: {min_temp:.0f}°...{max_temp:.0f}°C (feels {min_feel:.0f}°...{max_feel:.0f}°C)
WIND: {dominant_wind} {min_wind:.1f}–{max_wind:.1f} m/s ({wind_desc})
PRECIPITATION: {total_precip:.1f} mm
HUMIDITY: {min_hum:.0f}%–{max_hum:.0f}%
PRESSURE: {min_press} mmHg ({press_trend})

{status_block}

📊 Detailed chart attached.

---
Odesa Seaport Weather Bot | Auto-generated"""
    return body


def send_all(report, chart_path, subject):
    """Send via all configured channels."""
    print("\n" + "="*50)
    print("SENDING NOTIFICATIONS")
    print("="*50)

    # Email: formatted report + chart
    email_body = _format_email_body(report)
    send_email(subject, email_body, chart_path)

    # Telegram: same format as email + chart
    tg_message = _format_email_body(report)
    if report["alerts_en"]:
        tg_message += "\n\n" + "\n".join(f"⚠ {a}" for a in report["alerts_en"])
    send_telegram(tg_message, chart_path)

    # Webhook: structured JSON
    webhook_payload = {
        "location": "Odesa Seaport",
        "date": subject,
        "summary_en": report["short_en"],
        "summary_ru": report["short_ru"],
        "port_status": report["port_status"],
        "alerts": report["alerts_en"]
    }
    send_webhook(webhook_payload)

    print("="*50)
