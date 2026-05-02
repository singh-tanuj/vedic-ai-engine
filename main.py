# main.py
from fastapi import FastAPI, Query
import swisseph as swe
from datetime import datetime
from calculations import (
    get_dasha_details, get_dasha_timeline, 
    get_house_placements, get_planetary_strengths, 
    get_v2_varga_analysis, get_v3_ashtakavarga,
    get_v4_panchang, get_v5_agentic_summary
)

app = FastAPI(
    title="Vedic Agentic Engine",
    description="A Staff-level API for Agentic AI workflows in Vedic Astrology.",
    version="5.0.0"
)

PLANETS = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}

@app.get("/full-chart", tags=["Agent Tools"])
def get_full_chart(
    lat: float = Query(12.9716, description="Latitude of birth location"), 
    lon: float = Query(77.5946, description="Longitude of birth location")
):
    """
    Main tool for AI Agents. Returns a deterministic JSON map of the birth potential, 
    soul-strength (D9), environmental capacity (Ashtakavarga), and time-cycle (Dasha).
    """
    now = datetime.utcnow()
    jd = swe.julday(now.year, now.month, now.day, now.hour + (now.minute / 60))
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    _, ascmc = swe.houses_ex(jd, lat, lon, b'P') 
    lagna_sign = int(ascmc[0] / 30) + 1

    chart = {name: {"longitude": round(swe.calc_ut(jd, code, swe.FLG_SIDEREAL)[0][0], 4), "sign": int(swe.calc_ut(jd, code, swe.FLG_SIDEREAL)[0][0] / 30) + 1} for name, code in PLANETS.items()}
    k_lon = (chart["Rahu"]["longitude"] + 180) % 360
    chart["Ketu"] = {"longitude": round(k_lon, 4), "sign": int(k_lon / 30) + 1}

    # Data Calculation Layers
    panchang = get_v4_panchang(chart["Sun"]["longitude"], chart["Moon"]["longitude"], now)
    v3 = get_v3_ashtakavarga(chart, lagna_sign)
    v2 = get_v2_varga_analysis(chart)

    return {
        "agent_context": get_v5_agentic_summary(panchang, v3, v2), # Consumed by LLM
        "v4_panchang": panchang,
        "v3_ashtakavarga": v3,
        "v2_varga": v2,
        "v1_essentials": {
            "ascendant": lagna_sign,
            "strengths": get_planetary_strengths(chart, lagna_sign),
            "houses": get_house_placements(chart, lagna_sign),
            "dasha": get_dasha_timeline(now, chart["Moon"]["longitude"])
        }
    }