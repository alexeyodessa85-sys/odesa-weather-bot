"""
Text report generator for Odesa Seaport weather forecast.
Produces bilingual (EN/RU) short summary and detailed report.
"""

from datetime import datetime
from config.settings import (
    STORM_WIND_MPS, RESTRICTED_WIND_MPS,
    STORM_WAVE_M, RESTRICTED_WAVE_M,
    LOCATION_NAME, LOCATION_NAME_RU
)


def wind_description(speed_mps):
    """Get Beaufort-scale description."""
    if speed_mps < 0.3:
        return "Calm", "Штиль"
    elif speed_mps < 1.6:
        return "Light air", "Тихий"
    elif speed_mps < 3.4:
        return "Light breeze", "Лёгкий"
    elif speed_mps < 5.5:
        return "Gentle breeze", "Слабый"
    elif speed_mps < 8.0:
        return "Moderate breeze", "Умеренный"
    elif speed_mps < 10.8:
        return "Fresh breeze", "Свежий"
    elif speed_mps < 13.9:
        return "Strong breeze", "Сильный"
    elif speed_mps < 17.2:
        return "Near gale", "Крепкий"
    elif speed_mps < 20.8:
        return "Gale", "Очень крепкий"
    else:
        return "Storm", "Шторм"


def check_port_restrictions(max_wind, max_precip=0):
    """Check if port operations are restricted."""
    alerts_en = []
    alerts_ru = []
    status = "safe"

    if max_wind >= STORM_WIND_MPS:
        alerts_en.append(f"\u26a0 STORM ALERT: Wind {max_wind:.1f} m/s exceeds {STORM_WIND_MPS} m/s threshold. "
                        f"Vessel entry/exit PROHIBITED per Odesa Seaport Regulations.")
        alerts_ru.append(f"\u26a0 ШТОРМОВОЕ ПРЕДУПРЕЖДЕНИЕ: Ветер {max_wind:.1f} м/с превышает порог {STORM_WIND_MPS} м/с. "
                        f"Вход/выход судов ЗАПРЕЩЁН по правилам МТП Одесса.")
        status = "storm"
    elif max_wind >= RESTRICTED_WIND_MPS:
        alerts_en.append(f"\u26a0 RESTRICTION: Wind {max_wind:.1f} m/s exceeds {RESTRICTED_WIND_MPS} m/s. "
                        f"Towing required. Gas/chemical carriers and disabled vessels prohibited.")
        alerts_ru.append(f"\u26a0 ОГРАНИЧЕНИЯ: Ветер {max_wind:.1f} м/с превышает {RESTRICTED_WIND_MPS} м/с. "
                        f"Требуется буксировка. Газовозы и неисправные суда — запрет.")
        status = "restricted"

    return {
        "status": status,
        "alerts_en": alerts_en,
        "alerts_ru": alerts_ru
    }


def generate_report(weather_data):
    """
    Generate bilingual text report.

    Returns dict with:
        - short_en: one-line English summary
        - short_ru: one-line Russian summary
        - full_en: detailed English report
        - full_ru: detailed Russian report
        - port_status: safe / restricted / storm
    """
    data = weather_data
    temps = data["temps"]
    feels_like = data["feels_like"]
    wind_speed = data["wind_speed"]
    wind_dir = data["wind_dir"]
    humidity = data["humidity"]
    pressure = data["pressure"]
    precip = data["precip"]
    date_str = data.get("date_str", "")
    date_str_ru = data.get("date_str_ru", "")

    max_temp = max(temps)
    min_temp = min(temps)
    max_feel = max(feels_like)
    min_feel = min(feels_like)
    max_wind = max(wind_speed)
    min_wind = min(wind_speed)
    avg_wind = sum(wind_speed) / len(wind_speed)
    total_precip = sum(precip)
    max_humidity = max(humidity)
    min_humidity = min(humidity)
    dominant_wind = max(set(wind_dir), key=wind_dir.count)
    wind_desc_en, wind_desc_ru = wind_description(max_wind)

    # Port restrictions check
    restriction = check_port_restrictions(max_wind)
    status = restriction["status"]

    # --- SHORT SUMMARY (one line) ---
    short_en = (f"{date_str}: {min_temp:.0f}\u00b0...{max_temp:.0f}\u00b0C (feels {min_feel:.0f}\u00b0...{max_feel:.0f}\u00b0C), "
                f"wind {dominant_wind} {min_wind:.1f}\u2013{max_wind:.1f} m/s ({wind_desc_en}). "
                f"Precip: {total_precip:.1f} mm. Port: {status.upper()}.")
    short_ru = (f"{date_str_ru}: {min_temp:.0f}\u00b0...{max_temp:.0f}\u00b0C (ощущ. {min_feel:.0f}\u00b0...{max_feel:.0f}\u00b0C), "
                f"ветер {dominant_wind} {min_wind:.1f}\u2013{max_wind:.1f} м/с ({wind_desc_ru}). "
                f"Осадки: {total_precip:.1f} мм. Порт: {status.upper()}.")

    # --- FULL REPORT ---
    full_en = f"""{'='*60}
WEATHER FORECAST — {LOCATION_NAME}
{date_str}
{'='*60}

TEMPERATURE
  Range: {min_temp:.0f}°C ... {max_temp:.0f}°C
  Feels like: {min_feel:.0f}°C ... {max_feel:.0f}°C
  Warmest at: {data['hours'][temps.index(max_temp)]}
  Coolest at: {data['hours'][temps.index(min_temp)]}

WIND
  Direction: {dominant_wind} (dominant)
  Speed: {min_wind:.1f} – {max_wind:.1f} m/s (avg {avg_wind:.1f} m/s)
  Character: {wind_desc_en}

PRECIPITATION
  Total: {total_precip:.1f} mm
  Max intensity: {max(precip):.1f} mm at {data['hours'][precip.index(max(precip))]}

HUMIDITY
  Range: {min_humidity:.0f}% – {max_humidity:.0f}%

PRESSURE
  Range: {min(pressure):.0f} – {max(pressure):.0f} mmHg
  Trend: {'rising' if pressure[-1] > pressure[0] else 'falling' if pressure[-1] < pressure[0] else 'stable'}

PORT OPERATIONS STATUS: {status.upper()}
{'='*60}
"""

    if restriction["alerts_en"]:
        full_en += "\nALERTS:\n"
        for alert in restriction["alerts_en"]:
            full_en += f"  {alert}\n"
        full_en += "="*60 + "\n"

    full_ru = f"""{'='*60}
ПРОГНОЗ ПОГОДЫ — {LOCATION_NAME_RU}
{date_str_ru}
{'='*60}

ТЕМПЕРАТУРА
  Диапазон: {min_temp:.0f}°C ... {max_temp:.0f}°C
  Ощущается: {min_feel:.0f}°C ... {max_feel:.0f}°C
  Максимум в: {data['hours'][temps.index(max_temp)]}
  Минимум в: {data['hours'][temps.index(min_temp)]}

ВЕТЕР
  Направление: {dominant_wind} (преобладающее)
  Скорость: {min_wind:.1f} – {max_wind:.1f} м/с (средн. {avg_wind:.1f} м/с)
  Характер: {wind_desc_ru}

ОСАДКИ
  Всего: {total_precip:.1f} мм
  Макс. интенсивность: {max(precip):.1f} мм в {data['hours'][precip.index(max(precip))]}

ВЛАЖНОСТЬ
  Диапазон: {min_humidity:.0f}% – {max_humidity:.0f}%

ДАВЛЕНИЕ
  Диапазон: {min(pressure):.0f} – {max(pressure):.0f} мм рт.ст.
  Тенденция: {'повышение' if pressure[-1] > pressure[0] else 'понижение' if pressure[-1] < pressure[0] else 'стабильное'}

СТАТУС ПОРТОВЫХ ОПЕРАЦИЙ: {status.upper()}
{'='*60}
"""

    if restriction["alerts_ru"]:
        full_ru += "\nПРЕДУПРЕЖДЕНИЯ:\n"
        for alert in restriction["alerts_ru"]:
            full_ru += f"  {alert}\n"
        full_ru += "="*60 + "\n"

    return {
        "short_en": short_en,
        "short_ru": short_ru,
        "full_en": full_en,
        "full_ru": full_ru,
        "port_status": status,
        "alerts_en": restriction["alerts_en"],
        "alerts_ru": restriction["alerts_ru"],
        # Raw data for email formatting
        "date_str": date_str,
        "temps": temps,
        "feels_like": feels_like,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
        "precip": precip,
        "humidity": humidity,
        "pressure": pressure,
    }
