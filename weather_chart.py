"""
Weather Chart Generator for Odesa Seaport.
Generates a professional 3-panel forecast chart with LIGHT theme.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
from pathlib import Path
import os

# Font settings — Verdana, larger sizes
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Verdana', 'DejaVu Sans', 'Arial', 'Liberation Sans']
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 17
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['xtick.labelsize'] = 13
plt.rcParams['ytick.labelsize'] = 13
plt.rcParams['legend.fontsize'] = 11

from config.settings import (
    STORM_WIND_MPS, RESTRICTED_WIND_MPS,
    OUTPUT_DIR, LOCATION_NAME
)

# Light theme color palette
C_BG = "#F8FAFC"          # main background
C_PANEL = "#FFFFFF"       # panel background
C_GRID = "#E2E8F0"        # grid lines
C_TEXT = "#0F172A"        # primary text (dark)
C_TEXT_SEC = "#475569"    # secondary text
C_BORDER = "#CBD5E1"      # panel borders

C_TEMP = "#0369A1"        # temperature line (dark blue)
C_FEEL = "#94A3B8"        # feels-like (gray)
C_WIND_LIGHT = "#0284C7"  # light wind bar
C_WIND_MOD = "#F59E0B"    # moderate wind bar
C_WIND_STRONG = "#DC2626" # strong wind bar
C_PRECIP = "#3B82F6"      # precipitation
C_PRESSURE = "#059669"    # pressure
C_HUMIDITY = "#7C3AED"    # humidity

C_SAFE_ZONE = "#DCFCE7"   # green safe zone
C_RESTRICT_ZONE = "#FEF3C7"  # yellow restrict zone
C_STORM_ZONE = "#FEE2E2"  # red storm zone


def generate_chart(weather_data, output_path=None):
    data = weather_data
    hours = data["hours"]
    temps = data["temps"]
    feels_like = data["feels_like"]
    humidity = data["humidity"]
    pressure = data["pressure"]
    wind_speed_ms = data["wind_speed"]
    wind_dir = data["wind_dir"]
    precip = data["precip"]
    weather_desc = data["weather_desc"]
    date_str = data.get("date_str", "")

    if not hours:
        raise ValueError("No weather data provided")

    fig = plt.figure(figsize=(18, 17))
    fig.patch.set_facecolor(C_BG)
    gs = fig.add_gridspec(3, 1, height_ratios=[2.5, 1.7, 1.5], hspace=0.18)

    x = np.arange(len(hours))

    # HEADER
    title = f'WEATHER FORECAST — {LOCATION_NAME.upper()}\n{date_str}'
    fig.suptitle(title, fontsize=24, fontweight="bold", color=C_TEXT, y=0.98)
    fig.text(0.5, 0.935, "Source: Open-Meteo API  |  Port restrictions per Odesa Seaport Regulations",
             ha="center", fontsize=12, color=C_TEXT_SEC, style="italic")

    # PANEL 1: Temperature
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor(C_PANEL)
    ax1.set_xlim(-0.5, len(hours) - 0.5)
    y_min = min(min(feels_like, default=0) - 3, -2)
    y_max = max(max(temps, default=15) + 5, 18)
    ax1.set_ylim(y_min, y_max)

    for i in range(len(hours)):
        color = "#FFFFFF" if i % 2 == 0 else "#F8FAFC"
        ax1.axvspan(i - 0.5, i + 0.5, alpha=0.5, color=color)

    ax1.plot(x, temps, "o-", color=C_TEMP, linewidth=3.5, markersize=14,
             zorder=5, label="Temperature", markerfacecolor=C_TEMP,
             markeredgecolor="white", markeredgewidth=2)
    ax1.plot(x, feels_like, "s--", color=C_FEEL, linewidth=2.2, markersize=9,
             zorder=5, label="Feels like", markerfacecolor="#E2E8F0",
             markeredgecolor="white", markeredgewidth=1.5)
    ax1.fill_between(x, temps, alpha=0.08, color=C_TEMP)

    for i, (t, f) in enumerate(zip(temps, feels_like)):
        ax1.annotate(f"{int(round(t))}\u00b0", (i, t + 0.8), ha="center", va="bottom",
                    fontsize=20, fontweight="bold", color=C_TEXT)
        ax1.annotate(f"feels {int(round(f))}\u00b0", (i, f - 1.0), ha="center", va="top",
                    fontsize=13, color=C_TEXT_SEC)

    for i, desc in enumerate(weather_desc):
        ax1.annotate(desc, (i, y_max - 1), ha="center", va="center",
                    fontsize=10, color=C_TEXT_SEC, style="italic", fontweight="medium")

    ax1.set_xticks(x)
    ax1.set_xticklabels(hours, fontsize=13, color=C_TEXT, fontweight="bold")
    ax1.set_ylabel("Temperature, \u00b0C", fontsize=13, color=C_TEXT, fontweight="bold")
    ax1.tick_params(axis="y", colors=C_TEXT, labelsize=11)
    ax1.legend(loc="upper left", fontsize=11, facecolor=C_PANEL, edgecolor=C_BORDER,
              labelcolor=C_TEXT, framealpha=0.9)
    ax1.set_title("Hourly Temperature and Feels-Like Temperature", fontsize=15,
                 color=C_TEMP, fontweight="bold", pad=12)
    for spine in ax1.spines.values():
        spine.set_color(C_BORDER)
        spine.set_linewidth(1)
    ax1.grid(axis="y", alpha=0.4, color=C_GRID, linestyle="-")
    ax1.grid(axis="x", alpha=0.2, color=C_GRID, linestyle="-")

    # PANEL 2: Wind with Safety Zones
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor(C_PANEL)
    ax2.set_xlim(-0.5, len(hours) - 0.5)
    ax_max = max(max(wind_speed_ms, default=8) + 3, STORM_WIND_MPS + 3)
    ax2.set_ylim(0, ax_max)

    # Safety zone backgrounds
    ax2.axhspan(0, RESTRICTED_WIND_MPS, alpha=0.5, color=C_SAFE_ZONE, zorder=1)
    ax2.axhspan(RESTRICTED_WIND_MPS, STORM_WIND_MPS, alpha=0.5, color=C_RESTRICT_ZONE, zorder=1)
    ax2.axhspan(STORM_WIND_MPS, ax_max, alpha=0.5, color=C_STORM_ZONE, zorder=1)

    ax2.axhline(y=RESTRICTED_WIND_MPS, color="#D97706", linestyle="--", linewidth=2, alpha=0.9, zorder=3)
    ax2.axhline(y=STORM_WIND_MPS, color="#DC2626", linestyle="--", linewidth=2.5, alpha=0.95, zorder=3)

    ax2.text(len(hours) - 0.48, RESTRICTED_WIND_MPS + 0.2,
             f"RESTRICTED: towing required, gas/chemical carriers, disabled vessels ({RESTRICTED_WIND_MPS} m/s)",
             fontsize=11, color="#92400E", fontweight="bold", ha="right", va="bottom",
             bbox=dict(boxstyle="round,pad=0.3", facecolor=C_RESTRICT_ZONE, edgecolor="#D97706", alpha=0.95))
    ax2.text(len(hours) - 0.48, STORM_WIND_MPS + 0.2,
             f"⚠ STORM: vessel entry/exit PROHIBITED ({STORM_WIND_MPS} m/s)",
             fontsize=12, color="#991B1B", fontweight="bold", ha="right", va="bottom",
             bbox=dict(boxstyle="round,pad=0.4", facecolor=C_STORM_ZONE, edgecolor="#DC2626", alpha=0.95))

    for i in range(len(hours)):
        color = "#FFFFFF" if i % 2 == 0 else "#F8FAFC"
        ax2.axvspan(i - 0.5, i + 0.5, alpha=0.5, color=color)

    colors_wind = [C_WIND_STRONG if w >= 6 else C_WIND_MOD if w >= 4 else C_WIND_LIGHT for w in wind_speed_ms]
    bars = ax2.bar(x, wind_speed_ms, width=0.45, color=colors_wind, alpha=0.9,
                   edgecolor="white", linewidth=1, zorder=4)

    for i, (w, d) in enumerate(zip(wind_speed_ms, wind_dir)):
        ax2.annotate(f"{w:.1f}", (i, w + 0.2), ha="center", va="bottom",
                    fontsize=16, color=C_TEXT, fontweight="bold")
        ax2.annotate(f"m/s", (i, w + 0.2), ha="center", va="bottom",
                    fontsize=10, color=C_TEXT_SEC, xytext=(0, -16), textcoords="offset points")
        ax2.annotate(f"{d}", (i, -0.35), ha="center", va="top",
                    fontsize=13, color=C_TEXT_SEC, fontweight="bold")

    legend_elements = [
        mpatches.Patch(facecolor=C_WIND_LIGHT, alpha=0.9, label="Light (<4 m/s)"),
        mpatches.Patch(facecolor=C_WIND_MOD, alpha=0.9, label="Moderate (4–6 m/s)"),
        mpatches.Patch(facecolor=C_WIND_STRONG, alpha=0.9, label="Strong (≥6 m/s)"),
        plt.Line2D([0], [0], color="#D97706", linestyle="--", linewidth=2, label=f"Restricted ({RESTRICTED_WIND_MPS} m/s)"),
        plt.Line2D([0], [0], color="#DC2626", linestyle="--", linewidth=2.5, label=f"Storm threshold ({STORM_WIND_MPS} m/s)"),
    ]
    ax2.legend(handles=legend_elements, loc="upper left", fontsize=10,
              facecolor=C_PANEL, edgecolor=C_BORDER, labelcolor=C_TEXT, framealpha=0.9, ncol=2)

    ax2.set_xticks(x)
    ax2.set_xticklabels(hours, fontsize=13, color=C_TEXT, fontweight="bold")
    ax2.set_ylabel("Speed, m/s", fontsize=13, color=C_TEXT, fontweight="bold")
    ax2.tick_params(axis="y", colors=C_TEXT, labelsize=11)
    ax2.set_title("Wind Speed with Port Operation Safety Zones", fontsize=15,
                 color=C_WIND_LIGHT, fontweight="bold", pad=12)
    for spine in ax2.spines.values():
        spine.set_color(C_BORDER)
        spine.set_linewidth(1)
    ax2.grid(axis="y", alpha=0.3, color=C_GRID, linestyle="-")

    # PANEL 3: Humidity, Pressure, Precipitation
    ax3 = fig.add_subplot(gs[2])
    ax3.set_facecolor(C_PANEL)
    ax3.set_xlim(-0.5, len(hours) - 0.5)
    ax3.set_ylim(-0.5, max(max(precip, default=2) + 2, 7.5))

    for i in range(len(hours)):
        color = "#FFFFFF" if i % 2 == 0 else "#F8FAFC"
        ax3.axvspan(i - 0.5, i + 0.5, alpha=0.5, color=color)

    precip_colors = [C_PRECIP if pr > 0.5 else "#93C5FD" if pr > 0 else C_FEEL for pr in precip]
    bars_precip = ax3.bar(x - 0.18, precip, width=0.32, color=precip_colors, alpha=0.9,
                         edgecolor="white", linewidth=0.5, zorder=4)

    for i, pr in enumerate(precip):
        if pr > 0:
            ax3.annotate(f"{pr:.1f} mm", (i - 0.18, pr + 0.2), ha="center", va="bottom",
                        fontsize=12, color=C_PRECIP, fontweight="bold")
        else:
            ax3.annotate("\u2014", (i - 0.18, 0.3), ha="center", va="bottom",
                        fontsize=12, color=C_FEEL)

    ax3_twin1 = ax3.twinx()
    ax3_twin1.set_ylim(748, 758)
    ax3_twin1.plot(x, pressure, "D-", color=C_PRESSURE, linewidth=2.5, markersize=9,
                   label="Pressure", markerfacecolor=C_PRESSURE, markeredgecolor="white", markeredgewidth=1.5)
    for i, p in enumerate(pressure):
        ax3_twin1.annotate(f"{p}", (i, p + 0.4), ha="center", va="bottom",
                          fontsize=11, color=C_PRESSURE, fontweight="bold")

    ax3_twin2 = ax3.twinx()
    ax3_twin2.spines["right"].set_position(("outward", 65))
    ax3_twin2.set_ylim(25, 100)
    ax3_twin2.plot(x, humidity, "H-", color=C_HUMIDITY, linewidth=2.5, markersize=10,
                   label="Humidity", markerfacecolor=C_HUMIDITY, markeredgecolor="white", markeredgewidth=1.5)
    ax3_twin2.fill_between(x, humidity, alpha=0.08, color=C_HUMIDITY)
    for i, h in enumerate(humidity):
        ax3_twin2.annotate(f"{int(h)}%", (i, h + 2.5), ha="center", va="bottom",
                          fontsize=11, color=C_HUMIDITY, fontweight="bold")

    ax3.set_xticks(x)
    ax3.set_xticklabels(hours, fontsize=13, color=C_TEXT, fontweight="bold")
    ax3.set_ylabel("Precipitation, mm", fontsize=12, color=C_PRECIP, fontweight="bold")
    ax3.tick_params(axis="y", colors=C_PRECIP, labelsize=10)

    ax3_twin1.set_ylabel("Pressure, mmHg", fontsize=12, color=C_PRESSURE, fontweight="bold")
    ax3_twin1.tick_params(axis="y", colors=C_PRESSURE, labelsize=10)

    ax3_twin2.set_ylabel("Humidity, %", fontsize=12, color=C_HUMIDITY, fontweight="bold")
    ax3_twin2.tick_params(axis="y", colors=C_HUMIDITY, labelsize=10)

    ax3.set_title("Precipitation, Atmospheric Pressure and Relative Humidity", fontsize=15,
                 color=C_TEMP, fontweight="bold", pad=12)
    for spine in ax3.spines.values():
        spine.set_color(C_BORDER)
        spine.set_linewidth(1)
    for spine in ax3_twin1.spines.values():
        spine.set_color(C_BORDER)
        spine.set_linewidth(1)
    for spine in ax3_twin2.spines.values():
        spine.set_color(C_BORDER)
        spine.set_linewidth(1)

    lines1, labels1 = ax3_twin1.get_legend_handles_labels()
    lines2, labels2 = ax3_twin2.get_legend_handles_labels()
    ax3.legend([bars_precip] + lines1 + lines2,
              ["Precipitation"] + labels1 + labels2,
              loc="upper right", fontsize=9, facecolor=C_PANEL,
              edgecolor=C_BORDER, labelcolor=C_TEXT, framealpha=0.9)
    ax3.grid(axis="y", alpha=0.4, color=C_GRID, linestyle="-")

    fig.text(0.5, 0.005,
             "Data: Open-Meteo API  |  Port restrictions per Odesa Seaport Regulations  |  Auto-generated",
             ha="center", fontsize=9, color=C_TEXT_SEC)

    if output_path is None:
        date_slug = datetime.now().strftime("%Y_%m_%d")
        output_path = os.path.join(OUTPUT_DIR, f"weather_odessa_{date_slug}.png")

    plt.savefig(output_path, dpi=180, bbox_inches="tight",
                facecolor=C_BG, edgecolor="none")
    plt.close()
    return output_path
