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

# --- Data Constants ---
DASHA_DATA = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
    ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# --- Core V2 Varga Logic ---
def get_navamsa_sign(planet_lon: float) -> int:
    """Calculates the D-9 (Navamsa) sign based on sharding the 30-deg sign into 9 parts."""
    total_shards = int(planet_lon / (3.3333333333333335))
    d1_sign_idx = int(planet_lon / 30)
    shard_in_sign = total_shards % 9
    
    # Starting signs for Fire(1), Earth(10), Air(7), Water(4)
    cycle_start = [1, 10, 7, 4]
    start_sign = cycle_start[d1_sign_idx % 4]
    
    return (start_sign + shard_in_sign - 1) % 12 + 1

def get_v2_varga_analysis(chart: Dict) -> Dict[str, NavamsaDetail]:
    """Performs V2 dignity checks (Navamsa & Vargottama)."""
    results = {}
    for planet, data in chart.items():
        d1_sign = data["sign"]
        d9_sign = get_navamsa_sign(data["longitude"])
        is_vargottama = (d1_sign == d9_sign)
        
        results[planet] = NavamsaDetail(
            d9_sign=d9_sign,
            is_vargottama=is_vargottama,
            potency="High (Soul Aligned)" if is_vargottama else "Standard"
        )
    return results

# --- Existing Logic (Maintained for Continuity) ---
def get_dasha_details(moon_lon: float):
    n_size = 13.333333333333334
    n_idx = int(moon_lon / n_size)
    dasha_start_idx = n_idx % 9
    ruler, total_years = DASHA_DATA[dasha_start_idx]
    percent_passed = (moon_lon % n_size) / n_size
    remaining = total_years * (1 - percent_passed)
    return {
        "nakshatra": NAKSHATRAS[n_idx],
        "current_dasha_ruler": ruler,
        "remaining_years_in_first_dasha": round(remaining, 4),
        "nakshatra_completion_pct": round(percent_passed * 100, 2)
    }

def get_dasha_timeline(start_date, moon_lon: float):
    details = get_dasha_details(moon_lon)
    m_ruler = details['current_dasha_ruler']
    m_end = start_date + timedelta(days=details['remaining_years_in_first_dasha'] * 365.25)
    timeline = [{"period": m_ruler, "status": "Current", "ends_on": m_end.strftime("%Y-%m-%d")}]
    r_names = [d[0] for d in DASHA_DATA]
    curr_idx = r_names.index(m_ruler)
    next_date = m_end
    for i in range(1, 3):
        name, duration = DASHA_DATA[(curr_idx + i) % 9]
        next_date += timedelta(days=duration * 365.25)
        timeline.append({"period": name, "status": "Upcoming", "ends_on": next_date.strftime("%Y-%m-%d")})
    return timeline

def get_planetary_aspects(chart: Dict):
    aspects = {}
    rules = {"Sun": [7], "Moon": [7], "Mercury": [7], "Venus": [7], "Mars": [4, 7, 8], "Jupiter": [5, 7, 9], "Saturn": [3, 7, 10], "Rahu": [5, 7, 9], "Ketu": [5, 7, 9]}
    for planet, data in chart.items():
        target_signs = [(data["sign"] + step - 2) % 12 + 1 for step in rules.get(planet, [7])]
        aspects[planet] = target_signs
    return aspects

def get_house_placements(chart: Dict, lagna_sign: int):
    sig = {1: "Self", 2: "Wealth", 3: "Efforts", 4: "Home", 5: "Intelligence", 6: "Enemies", 7: "Partnerships", 8: "Transformation", 9: "Fortune", 10: "Career", 11: "Gains", 12: "Losses"}
    return {p: HouseDetail(house=(d["sign"] - lagna_sign) % 12 + 1, domain=sig[(d["sign"] - lagna_sign) % 12 + 1]) for p, d in chart.items()}

def get_planetary_strengths(chart: Dict, lagna_sign: int):
    dig_map = {"Jupiter": 1, "Mercury": 1, "Moon": 4, "Venus": 4, "Saturn": 7, "Rahu": 7, "Sun": 10, "Mars": 10}
    strengths = {}
    for planet, data in chart.items():
        house = (data["sign"] - lagna_sign) % 12 + 1
        p_score = 1.5 if house in [1, 4, 7, 10] else 1.0
        d_score = 2.0 if house == dig_map.get(planet) else 1.0
        total = p_score * d_score
        strengths[planet] = PlanetStrength(positional_score=p_score, directional_score=d_score, total_weighted_strength=round(total, 2), status="Strong" if total >= 2.0 else "Average")
    return strengths