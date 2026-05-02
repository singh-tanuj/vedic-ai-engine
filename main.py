# main.py
from fastapi import FastAPI, Query
import swisseph as swe
from datetime import datetime
from calculations import (
    get_dasha_details, get_dasha_timeline, 
    get_planetary_aspects, get_house_placements,
    get_planetary_strengths, get_v2_varga_analysis,
    get_v3_ashtakavarga
)

app = FastAPI()

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
}

@app.get("/")
def home():
    return {"status": "V3 Vedic Engine Online", "modules": ["D1", "D9", "Ashtakavarga", "Dasha"]}

@app.get("/full-chart")
def get_full_chart(
    lat: float = Query(12.9716, description="Latitude"), 
    lon: float = Query(77.5946, description="Longitude")
):
    now = datetime.utcnow()
    jd = swe.julday(now.year, now.month, now.day, now.hour + (now.minute / 60))
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # 1. Ascendant Logic
    _, ascmc = swe.houses_ex(jd, lat, lon, b'P') 
    lagna_sign = int(ascmc[0] / 30) + 1

    # 2. Planetary Array
    chart = {}
    for name, code in PLANETS.items():
        res, _ = swe.calc_ut(jd, code, swe.FLG_SIDEREAL)
        chart[name] = {"longitude": round(res[0], 4), "sign": int(res[0] / 30) + 1}
    
    # Ketu Derivation
    k_lon = (chart["Rahu"]["longitude"] + 180) % 360
    chart["Ketu"] = {"longitude": round(k_lon, 4), "sign": int(k_lon / 30) + 1}

    # 3. Production Intelligence Orchestration (V3)
    return {
        "metadata": {"timestamp": now, "v_level": "3.0 (Ashtakavarga)"},
        "ascendant": {"longitude": round(ascmc[0], 4), "sign": lagna_sign},
        "v3_ashtakavarga_heat_map": get_v3_ashtakavarga(chart, lagna_sign), # NEW
        "varga_d9_analysis": get_v2_varga_analysis(chart),
        "planetary_strengths": get_planetary_strengths(chart, lagna_sign),
        "house_analysis": get_house_placements(chart, lagna_sign),
        "aspect_connections": get_planetary_aspects(chart),
        "dasha_system": {
            "details": get_dasha_details(chart["Moon"]["longitude"]),
            "timeline": get_dasha_timeline(now, chart["Moon"]["longitude"])
        }
    }