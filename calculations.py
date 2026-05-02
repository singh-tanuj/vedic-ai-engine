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

# --- V3: Ashtakavarga Heatmap Logic ---
def get_v3_ashtakavarga(chart: Dict, lagna_sign: int) -> Dict[str, AshtakavargaDetail]:
    """
    Calculates a numeric scoring system (0-8) for each planet's house.
    Acts as a 'Load Test' for the planetary energy in that life domain.
    """
    results = {}
    for planet, data in chart.items():
        # Calculate house based on Lagna
        house = (data["sign"] - lagna_sign) % 12 + 1
        
        # Scoring Algorithm (Implementation for V3)
        # 4 is the neutral threshold. >5 is high-capacity, <4 is low-capacity.
        base_score = 4 
        
        # Upachaya (Growth) houses naturally accumulate more points
        if house in [3, 6, 10, 11]: 
            base_score += 1
        
        # Dharma (Purpose) houses provide environmental alignment
        if house in [1, 5, 9]:
            base_score += 1
            
        # Specific planet/house synergies for V3
        if planet == "Jupiter" and house == 5: base_score += 1
        if planet == "Saturn" and house == 8: base_score += 1

        results[planet] = AshtakavargaDetail(
            score=base_score,
            intensity="High" if base_score > 5 else "Moderate" if base_score >= 4 else "Low"
        )
    return results

# --- V2: Navamsa Logic ---
def get_navamsa_sign(planet_lon: float) -> int:
    total_shards = int(planet_lon / (3.3333333333333335))
    d1_sign_idx = int(planet_lon / 30)
    shard_in_sign = total_shards % 9
    cycle_start = [1, 10, 7, 4]
    start_sign = cycle_start[d1_sign_idx % 4]
    return (start_sign + shard_in_sign - 1) % 12 + 1

def get_v2_varga_analysis(chart: Dict) -> Dict[str, NavamsaDetail]:
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

# --- Foundation Logic (V1) ---
def get_dasha_details(moon_lon: float):
    n_size = 13.333333333333334
    n_idx = int(moon_lon / n_size)
    ruler, total_years = DASHA_DATA[n_idx % 9]
    percent_passed = (moon_lon % n_size) / n_size
    return {
        "nakshatra": NAKSHATRAS[n_idx],
        "current_dasha_ruler": ruler,
        "remaining_years_in_first_dasha": round(total_years * (1 - percent_passed), 4),
        "nakshatra_completion_pct": round(percent_passed * 100, 2)
    }

def get_dasha_timeline(start_date, moon_lon: float):
    details = get_dasha_details(moon_lon)
    m_end = start_date + timedelta(days=details['remaining_years_in_first_dasha'] * 365.25)
    timeline = [{"period": details['current_dasha_ruler'], "status": "Current", "ends_on": m_end.strftime("%Y-%m-%d")}]
    r_names = [d[0] for d in DASHA_DATA]
    curr_idx = r_names.index(details['current_dasha_ruler'])
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
        aspects[planet] = [(data["sign"] + step - 2) % 12 + 1 for step in rules.get(planet, [7])]
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
        strengths[planet] = PlanetStrength(
            positional_score=p_score,
            directional_score=d_score,
            total_weighted_strength=round(p_score * d_score, 2),
            status="Strong" if p_score * d_score >= 2.0 else "Average"
        )
    return strengths