# main.py
from fastapi import FastAPI, Query
import swisseph as swe
from datetime import datetime
from calculations import (
    get_complete_varga_profile, get_v4_panchang, 
    get_planetary_strengths
)

app = FastAPI(title="Vedic Shodashvarga Engine (V6)")

PLANETS = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}

@app.get("/full-analysis")
def get_analysis(
    lat: float = Query(12.9716, description="Latitude"), 
    lon: float = Query(77.5946, description="Longitude")
):
    now = datetime.utcnow()
    jd = swe.julday(now.year, now.month, now.day, now.hour + (now.minute / 60))
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # 1. Base Positions
    chart = {}
    for name, code in PLANETS.items():
        res, _ = swe.calc_ut(jd, code, swe.FLG_SIDEREAL)
        chart[name] = {"longitude": round(res[0], 4), "sign": int(res[0] / 30) + 1}
    
    k_lon = (chart["Rahu"]["longitude"] + 180) % 360
    chart["Ketu"] = {"longitude": round(k_lon, 4), "sign": int(k_lon / 30) + 1}

    # 2. Ascendant
    _, ascmc = swe.houses_ex(jd, lat, lon, b'P') 
    lagna_sign = int(ascmc[0] / 30) + 1

    return {
        "metadata": {"version": "6.0", "timestamp": now},
        "panchang": get_v4_panchang(chart["Sun"]["longitude"], chart["Moon"]["longitude"], now),
        "d1_positions": chart,
        "shodashvarga_profile": get_complete_varga_profile(chart),
        "strengths": get_planetary_strengths(chart, lagna_sign)
    }