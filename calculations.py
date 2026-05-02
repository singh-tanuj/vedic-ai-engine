# calculations.py
from datetime import timedelta
from pydantic import BaseModel
from typing import Dict, List, Optional

# --- Pydantic Schemas for Deterministic Output ---
class PlanetStrength(BaseModel):
    positional_score: float
    directional_score: float
    total_weighted_strength: float
    status: str

class HouseDetail(BaseModel):
    house: int
    domain: str

class NavamsaDetail(BaseModel):
    d9_sign: int
    is_vargottama: bool
    potency: str

class AshtakavargaDetail(BaseModel):
    score: int
    intensity: str

class PanchangDetail(BaseModel):
    vara: str
    tithi: int
    tithi_name: str
    phase: str 

# --- Data Constants ---
TITHI_NAMES = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"]
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DASHA_DATA = [("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

# --- New V5: Agentic Narrative Helper ---
def get_v5_agentic_summary(panchang: PanchangDetail, v3: Dict, v2: Dict) -> str:
    """Consolidates complex data into a summary string for LLM context."""
    strongest = [p for p, d in v3.items() if d.intensity == "High"]
    vargottama = [p for p, d in v2.items() if d.is_vargottama]
    
    return f"Environment is {panchang.tithi_name} ({panchang.phase}). " \
           f"Key strengths identified in {', '.join(strongest)}. " \
           f"Soul-aligned (Vargottama) planets: {', '.join(vargottama) if vargottama else 'None'}."

# --- Existing Logic (D1, D9, Ashtakavarga, Panchang) ---
def get_v4_panchang(sun_lon: float, moon_lon: float, timestamp) -> PanchangDetail:
    vara = DAYS[timestamp.weekday()]
    diff = (moon_lon - sun_lon + 360) % 360
    tithi_num = int(diff / 12) + 1
    return PanchangDetail(vara=vara, tithi=tithi_num, tithi_name=TITHI_NAMES[(tithi_num - 1) % 15], phase="Shukla" if diff < 180 else "Krishna")

def get_v3_ashtakavarga(chart: Dict, lagna_sign: int) -> Dict[str, AshtakavargaDetail]:
    results = {}
    for planet, data in chart.items():
        house = (data["sign"] - lagna_sign) % 12 + 1
        score = 4
        if house in [3, 6, 10, 11]: score += 1
        if house in [1, 5, 9]: score += 1
        results[planet] = AshtakavargaDetail(score=score, intensity="High" if score > 5 else "Moderate" if score >= 4 else "Low")
    return results

def get_navamsa_sign(planet_lon: float) -> int:
    total_shards = int(planet_lon / (3.3333333333333335))
    start_sign = [1, 10, 7, 4][int(planet_lon / 30) % 4]
    return (start_sign + (total_shards % 9) - 1) % 12 + 1

def get_v2_varga_analysis(chart: Dict) -> Dict[str, NavamsaDetail]:
    return {p: NavamsaDetail(d9_sign=get_navamsa_sign(d["longitude"]), is_vargottama=(d["sign"] == get_navamsa_sign(d["longitude"])), potency="High" if (d["sign"] == get_navamsa_sign(d["longitude"])) else "Standard") for p, d in chart.items()}

def get_dasha_details(moon_lon: float):
    n_idx = int(moon_lon / 13.333333333333334)
    ruler, years = DASHA_DATA[n_idx % 9]
    rem = years * (1 - ((moon_lon % 13.333333333333334) / 13.333333333333334))
    return {"nakshatra": NAKSHATRAS[n_idx], "current_dasha_ruler": ruler, "remaining_years": round(rem, 4)}

def get_dasha_timeline(start_date, moon_lon: float):
    det = get_dasha_details(moon_lon)
    m_end = start_date + timedelta(days=det['remaining_years'] * 365.25)
    return [{"period": det['current_dasha_ruler'], "status": "Current", "ends_on": m_end.strftime("%Y-%m-%d")}]

def get_house_placements(chart: Dict, lagna_sign: int):
    sig = {1: "Self", 2: "Wealth", 3: "Efforts", 4: "Home", 5: "Intelligence", 6: "Enemies", 7: "Partnerships", 8: "Transformation", 9: "Fortune", 10: "Career", 11: "Gains", 12: "Losses"}
    return {p: HouseDetail(house=(d["sign"] - lagna_sign) % 12 + 1, domain=sig[(d["sign"] - lagna_sign) % 12 + 1]) for p, d in chart.items()}

def get_planetary_strengths(chart: Dict, lagna_sign: int):
    dig = {"Jupiter": 1, "Mercury": 1, "Moon": 4, "Venus": 4, "Saturn": 7, "Rahu": 7, "Sun": 10, "Mars": 10}
    res = {}
    for p, d in chart.items():
        h = (d["sign"] - lagna_sign) % 12 + 1
        s = (1.5 if h in [1, 4, 7, 10] else 1.0) * (2.0 if h == dig.get(p) else 1.0)
        res[p] = PlanetStrength(positional_score=1.5 if h in [1, 4, 7, 10] else 1.0, directional_score=2.0 if h == dig.get(p) else 1.0, total_weighted_strength=s, status="Strong" if s >= 2.0 else "Average")
    return res