#!/usr/bin/env python3
"""
Odesa Seaport Daily Weather Forecast
=====================================
Fetches weather data from Open-Meteo API, generates a chart,
creates a bilingual report, and sends via configured channels.

Usage:
    python weather_forecast.py           # run for tomorrow
    python weather_forecast.py --today   # run for today
    python weather_forecast.py --date 2026-04-21  # specific date
"""

import os
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Auto-load .env
_PROJECT_DIR = Path(__file__).resolve().parent
_ENV_FILE = _PROJECT_DIR / ".env"
if _ENV_FILE.exists():
    with open(_ENV_FILE) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)

from config.settings import (
    LATITUDE, LONGITUDE, OUTPUT_DIR,
    WEATHER_API_URL
)
from weather_chart import generate_chart
from weather_report import generate_report
from sender import send_all


def fetch_weather(target_date=None):
    """
    Fetch hourly forecast from Open-Meteo for Odesa port.

    Parameters:
        target_date: datetime.date object. If None, uses tomorrow.

    Returns:
        dict with formatted weather data.
    """
    if target_date is None:
        target_date = datetime.now().date() + timedelta(days=1)

    date_str = target_date.isoformat()
    print(f"[Fetch] Getting forecast for {date_str} at {LATITUDE}, {LONGITUDE}")

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation",
            "weather_code",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m"
        ],
        "timezone": "Europe/Kiev",
        "wind_speed_unit": "ms"
    }

    try:
        resp = requests.get(WEATHER_API_URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch weather: {e}")

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    feels = hourly.get("apparent_temperature", [])
    humidity = hourly.get("relative_humidity_2m", [])
    precip = hourly.get("precipitation", [])
    weather_codes = hourly.get("weather_code", [])
    pressure = hourly.get("surface_pressure", [])
    wind_spd = hourly.get("wind_speed_10m", [])
    wind_dir_deg = hourly.get("wind_direction_10m", [])

    if not times:
        raise RuntimeError("No forecast data returned from API")

    # WMO weather code descriptions
    WMO_CODES = {
        0: ("Clear", "Clear"),
        1: ("Mainly clear", "Mostly clear"),
        2: ("Partly cloudy", "Partly cloudy"),
        3: ("Overcast", "Cloudy"),
        45: ("Fog", "Fog"),
        48: ("Depositing rime fog", "Fog"),
        51: ("Light drizzle", "Light rain"),
        53: ("Moderate drizzle", "Rain"),
        55: ("Dense drizzle", "Rain"),
        56: ("Light freezing drizzle", "Freezing rain"),
        57: ("Dense freezing drizzle", "Freezing rain"),
        61: ("Slight rain", "Light rain"),
        63: ("Moderate rain", "Rain"),
        65: ("Heavy rain", "Heavy rain"),
        66: ("Light freezing rain", "Freezing rain"),
        67: ("Heavy freezing rain", "Freezing rain"),
        71: ("Slight snow fall", "Light snow"),
        73: ("Moderate snow fall", "Snow"),
        75: ("Heavy snow fall", "Snow"),
        77: ("Snow grains", "Snow"),
        80: ("Slight rain showers", "Showers"),
        81: ("Moderate rain showers", "Showers"),
        82: ("Violent rain showers", "Heavy showers"),
        85: ("Slight snow showers", "Snow showers"),
        86: ("Heavy snow showers", "Snow showers"),
        95: ("Thunderstorm", "Thunderstorm"),
        96: ("Thunderstorm with hail", "Thunderstorm"),
        99: ("Thunderstorm with heavy hail", "Thunderstorm"),
    }

    def deg_to_compass(deg):
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        ix = round(deg / 22.5) % 16
        return dirs[ix]

    # Select every 3rd hour for 8 data points (00, 03, 06, 09, 12, 15, 18, 21)
    indices = list(range(0, 24, 3))

    hours = []
    temps_out = []
    feels_out = []
    humidity_out = []
    pressure_out = []
    wind_spd_out = []
    wind_dir_out = []
    precip_out = []
    weather_desc = []

    for i in indices:
        if i >= len(times):
            break
        t = times[i]
        hour = t.split("T")[1][:5] if "T" in t else t
        hours.append(hour)
        temps_out.append(temps[i] if i < len(temps) else 0)
        feels_out.append(feels[i] if i < len(feels) else 0)
        humidity_out.append(humidity[i] if i < len(humidity) else 0)
        # Convert hPa to mmHg (1 hPa = 0.750062 mmHg)
        p_hpa = pressure[i] if i < len(pressure) else 750
        pressure_out.append(round(p_hpa * 0.750062))
        wind_spd_out.append(wind_spd[i] if i < len(wind_spd) else 0)
        wd = wind_dir_deg[i] if i < len(wind_dir_deg) else 0
        wind_dir_out.append(deg_to_compass(wd))
        precip_out.append(precip[i] if i < len(precip) else 0)
        code = weather_codes[i] if i < len(weather_codes) else 0
        desc, _ = WMO_CODES.get(code, ("Unknown", "Unknown"))
        weather_desc.append(desc)

    # Date strings
    weekday_en = target_date.strftime("%A")
    month_en = target_date.strftime("%B")
    date_str = f"{month_en} {target_date.day}, {target_date.year}  \u2022  {weekday_en}"

    # Russian weekday/month
    WEEKDAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг",
                   "Пятница", "Суббота", "Воскресенье"]
    MONTHS_RU = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                 "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    weekday_ru = WEEKDAYS_RU[target_date.weekday()]
    month_ru = MONTHS_RU[target_date.month]
    date_str_ru = f"{target_date.day} {month_ru} {target_date.year} г.  \u2022  {weekday_ru}"

    return {
        "hours": hours,
        "temps": temps_out,
        "feels_like": feels_out,
        "humidity": humidity_out,
        "pressure": pressure_out,
        "wind_speed": wind_spd_out,
        "wind_dir": wind_dir_out,
        "precip": precip_out,
        "weather_desc": weather_desc,
        "date_str": date_str,
        "date_str_ru": date_str_ru,
        "raw_date": date_str
    }


def main():
    parser = argparse.ArgumentParser(description="Odesa Seaport Weather Forecast")
    parser.add_argument("--today", action="store_true", help="Forecast for today instead of tomorrow")
    parser.add_argument("--date", type=str, help="Specific date (YYYY-MM-DD)")
    parser.add_argument("--no-send", action="store_true", help="Generate only, do not send")
    parser.add_argument("--chart-only", action="store_true", help="Generate chart only")
    args = parser.parse_args()

    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    elif args.today:
        target_date = datetime.now().date()
    else:
        target_date = datetime.now().date() + timedelta(days=1)

    print("="*60)
    print("ODESSA SEAPORT WEATHER FORECAST SYSTEM")
    print("="*60)
    print(f"Target date: {target_date}")
    print(f"Location: 46.4857°N, 30.7438°E (Odesa Seaport)")
    print("-"*60)

    # 1. Fetch data
    try:
        weather_data = fetch_weather(target_date)
        print(f"[OK] Fetched {len(weather_data['hours'])} hourly data points")
    except Exception as e:
        print(f"[ERROR] Failed to fetch weather: {e}")
        return 1

    # 2. Generate chart
    date_slug = target_date.strftime("%Y_%m_%d")
    chart_path = Path(OUTPUT_DIR) / f"weather_odessa_{date_slug}.png"
    try:
        generate_chart(weather_data, str(chart_path))
        print(f"[OK] Chart saved to {chart_path}")
    except Exception as e:
        print(f"[ERROR] Failed to generate chart: {e}")
        return 1

    if args.chart_only:
        print("[OK] Chart-only mode, done.")
        return 0

    # 3. Generate report
    report = generate_report(weather_data)
    print(f"[OK] Report generated")
    print(f"     Status: {report['port_status'].upper()}")
    if report["alerts_en"]:
        for alert in report["alerts_en"]:
            print(f"     ALERT: {alert}")

    # Print text preview
    print("\n" + "-"*60)
    print("SHORT SUMMARY (EN):", report["short_en"])
    print("SHORT SUMMARY (RU):", report["short_ru"])
    print("-"*60)

    # 4. Send notifications
    if not args.no_send:
        subject = f"Odesa Seaport Weather — {weather_data['date_str']}"
        send_all(report, str(chart_path), subject)
    else:
        print("[SKIP] Sending disabled (--no-send)")

    print("\n[OK] Done!")
    print("="*60)
    return 0


if __name__ == "__main__":
    exit(main())
