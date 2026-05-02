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

def get_antardashas(mahadasha_ruler: str, mahadasha_end_date):
    ruler_names = [d[0] for d in DASHA_DATA]
    ruler_durations = {d[0]: d[1] for d in DASHA_DATA}
    m_years = ruler_durations[mahadasha_ruler]
    start_idx = ruler_names.index(mahadasha_ruler)
    m_start_date = mahadasha_end_date - timedelta(days=m_years * 365.25)
    
    antardashas = []
    current_pointer = m_start_date
    for i in range(9):
        sub_ruler, sub_years = DASHA_DATA[(start_idx + i) % 9]
        ad_years = (m_years * sub_years) / 120
        next_pointer = current_pointer + timedelta(days=ad_years * 365.25)
        antardashas.append({"sub_period": f"{mahadasha_ruler}-{sub_ruler}", "ends_on": next_pointer.strftime("%Y-%m-%d")})
        current_pointer = next_pointer
    return antardashas

def get_dasha_timeline(start_date, moon_lon: float):
    details = get_dasha_details(moon_lon)
    m_ruler = details['current_dasha_ruler']
    m_end = start_date + timedelta(days=details['remaining_years_in_first_dasha'] * 365.25)
    
    timeline = [{
        "period": m_ruler,
        "status": "Current",
        "ends_on": m_end.strftime("%Y-%m-%d"),
        "sub_periods": get_antardashas(m_ruler, m_end)
    }]
    
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
    significance = {1: "Self/Identity", 2: "Wealth/Speech", 3: "Efforts/Siblings", 4: "Home/Mother", 5: "Intelligence/Children", 6: "Debt/Enemies", 7: "Partnerships/Marriage", 8: "Transformation/Longevity", 9: "Fortune/Philosophy", 10: "Career/Status", 11: "Gains/Social Circle", 12: "Losses/Spirituality"}
    return {p: HouseDetail(house=(d["sign"] - lagna_sign) % 12 + 1, domain=significance[(d["sign"] - lagna_sign) % 12 + 1]) for p, d in chart.items()}

def get_planetary_strengths(chart: Dict, lagna_sign: int):
    """Calculates Sthana (Positional) and Dig (Directional) Bala."""
    dig_bala_map = {"Jupiter": 1, "Mercury": 1, "Moon": 4, "Venus": 4, "Saturn": 7, "Rahu": 7, "Sun": 10, "Mars": 10}
    strengths = {}
    for planet, data in chart.items():
        house = (data["sign"] - lagna_sign) % 12 + 1
        p_score = 1.5 if house in [1, 4, 7, 10] else 1.0
        d_score = 2.0 if house == dig_bala_map.get(planet) else 1.0
        total = p_score * d_score
        strengths[planet] = PlanetStrength(
            positional_score=p_score,
            directional_score=d_score,
            total_weighted_strength=round(total, 2),
            status="Strong" if total >= 2.0 else "Average" if total >= 1.0 else "Weak"
        )
    return strengths