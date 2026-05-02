# calculations.py
from datetime import timedelta
from pydantic import BaseModel
from typing import Dict, List, Optional

# --- Pydantic Schemas ---
class VargaAnalysis(BaseModel):
    d2_hora: int
    d3_drekkana: int
    d4_chaturtamsa: int
    d7_saptamsa: int
    d9_navamsa: int
    d10_dasamsa: int
    d12_dwadasamsa: int
    d16_shodasamsa: int
    d24_siddhamsa: int
    d60_shashtiamsa: int

class PlanetStrength(BaseModel):
    positional_score: float
    directional_score: float
    total_weighted_strength: float
    status: str

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

# --- Universal Varga Engine ---
def get_varga_sign(planet_lon: float, division: int) -> int:
    """
    Generalized sharding logic for Shodashvarga (Divisional Charts).
    """
    shard_size = 30.0 / division
    sign_idx = int(planet_lon / 30)
    lon_in_sign = planet_lon % 30
    shard_idx = int(lon_in_sign / shard_size)
    
    # Specific starting rules for non-sequential charts
    if division == 2: # Hora
        is_odd = (sign_idx + 1) % 2 != 0
        if is_odd: return 5 if shard_idx == 0 else 4 # Leo then Cancer
        return 4 if shard_idx == 0 else 5 # Cancer then Leo
            
    elif division == 3: # Drekkana
        return (sign_idx + (shard_idx * 4)) % 12 + 1
        
    elif division == 7: # Saptamsa
        start = sign_idx if (sign_idx % 2 == 0) else (sign_idx + 6)
        return (start + shard_idx) % 12 + 1
        
    elif division == 9: # Navamsa
        cycle_start = [1, 10, 7, 4]
        start_sign = cycle_start[sign_idx % 4]
        return (start_sign + shard_idx - 1) % 12 + 1

    elif division == 10: # Dasamsa
        start = sign_idx if (sign_idx % 2 == 0) else (sign_idx + 8)
        return (start + shard_idx) % 12 + 1
        
    # Default sequential for D12, D16, D24, D60
    return (sign_idx + shard_idx) % 12 + 1

def get_complete_varga_profile(chart: Dict) -> Dict[str, VargaAnalysis]:
    profile = {}
    for planet, data in chart.items():
        lon = data["longitude"]
        profile[planet] = VargaAnalysis(
            d2_hora=get_varga_sign(lon, 2),
            d3_drekkana=get_varga_sign(lon, 3),
            d4_chaturtamsa=get_varga_sign(lon, 4),
            d7_saptamsa=get_varga_sign(lon, 7),
            d9_navamsa=get_varga_sign(lon, 9),
            d10_dasamsa=get_varga_sign(lon, 10),
            d12_dwadasamsa=get_varga_sign(lon, 12),
            d16_shodasamsa=get_varga_sign(lon, 16),
            d24_siddhamsa=get_varga_sign(lon, 24),
            d60_shashtiamsa=get_varga_sign(lon, 60)
        )
    return profile

# --- Supporting Logic ---
def get_v4_panchang(sun_lon: float, moon_lon: float, timestamp) -> PanchangDetail:
    vara = DAYS[timestamp.weekday()]
    diff = (moon_lon - sun_lon + 360) % 360
    tithi_num = int(diff / 12) + 1
    return PanchangDetail(vara=vara, tithi=tithi_num, tithi_name=TITHI_NAMES[(tithi_num - 1) % 15], phase="Shukla" if diff < 180 else "Krishna")

def get_planetary_strengths(chart: Dict, lagna_sign: int):
    dig = {"Jupiter": 1, "Mercury": 1, "Moon": 4, "Venus": 4, "Saturn": 7, "Rahu": 7, "Sun": 10, "Mars": 10}
    res = {}
    for p, d in chart.items():
        h = (d["sign"] - lagna_sign) % 12 + 1
        s = (1.5 if h in [1, 4, 7, 10] else 1.0) * (2.0 if h == dig.get(p) else 1.0)
        res[p] = PlanetStrength(positional_score=1.5 if h in [1, 4, 7, 10] else 1.0, directional_score=2.0 if h == dig.get(p) else 1.0, total_weighted_strength=s, status="Strong" if s >= 2.0 else "Average")
    return res