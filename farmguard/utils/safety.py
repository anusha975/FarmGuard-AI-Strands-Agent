"""
Responsible AI & Agricultural Safety Disclaimers and Validation Guards.
"""
from typing import Tuple

SAFETY_DISCLAIMER_EN = (
    "⚠️ RESPONSIBLE AI & AGRICULTURAL SAFETY NOTICE: "
    "FarmGuard AI provides advisory risk evaluations synthesized from meteorological forecasts "
    "and agro-hydrological models (FAO-56). Unforeseen micro-climates, soil depth variations, and pest outbreaks "
    "can alter local conditions. Smallholder farmers must verify these automated recommendations with local "
    "Agricultural Extension Officers (e.g. Rythu Vedika / Krishi Vigyan Kendra (KVK) / Agricultural Extension Officers (AEO) / "
    "PJTSAU University Agronomists / Rythu Bharosa Kendra) before making major financial, planting, or agrochemical commitments."
)

SAFETY_DISCLAIMER_TE = (
    "⚠️ బాధ్యతాయుతమైన ఏఐ & వ్యవసాయ భద్రతా సమాచారం: "
    "ఫామ్‌గార్డ్ ఏఐ (FarmGuard AI) అందించే సలహాలు వాతావరణ అంచనాలు మరియు ఎఫ్.ఎ.ఓ-56 శాస్త్రీయ నమూనాల ఆధారంగా రూపొందించబడ్డాయి. "
    "స్థానిక నేల స్వభావం, భూమి లోతు మరియు తెగుళ్ల తీవ్రతను బట్టి క్షేత్రస్థాయి పరిస్థితులు మారవచ్చు. "
    "రైతు సోదరులు ఏదైనా పెద్ద ఆర్థిక లేదా రసాయన వినియోగ నిర్ణయాలు తీసుకునే ముందు స్థానిక వ్యవసాయ విస్తరణ అధికారులు "
    "(రైతు వేదిక / ఏఈఓ / కేవీకే / ప్రొఫెసర్ జయశంకర్ తెలంగాణ వ్యవసాయ విశ్వవిద్యాలయ శాస్త్రవేత్తలు / రైతు భరోసా కేంద్రం) సలహా తీసుకోవాలని మనవి."
)

def get_safety_disclaimer(language: str = "en") -> str:
    """Return language-specific agricultural safety disclaimer."""
    return SAFETY_DISCLAIMER_TE if language.lower() in ["te", "telugu"] else SAFETY_DISCLAIMER_EN

def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """Validate decimal latitude and longitude bounds."""
    if not (-90.0 <= lat <= 90.0):
        return False, f"Latitude {lat} is out of valid bounds [-90, 90]."
    if not (-180.0 <= lon <= 180.0):
        return False, f"Longitude {lon} is out of valid bounds [-180, 180]."
    return True, "Valid"

