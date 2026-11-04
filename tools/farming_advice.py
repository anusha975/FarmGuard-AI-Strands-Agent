"""
Actionable Farming Recommendations and Bilingual Advisory Tool for FarmGuard AI.
Uses the official AWS Strands Agents SDK @tool decorator.
Supports English and Telugu (తెలుగు) localization with agricultural safety guidelines.
"""
import json
from strands import tool
from farmguard.data.crop_knowledge import CROP_DATABASE
from farmguard.data.telugu_translations import (
    TELUGU_CROPS,
    TELUGU_STAGES,
    TELUGU_RISK_LEVELS,
    TELUGU_COMMON_ADVICE
)
from farmguard.utils.safety import get_safety_disclaimer

@tool
def get_farming_recommendations(
    crop_name: str,
    growth_stage: str,
    drought_level: str,
    soil_deficit_mm: float,
    heatwave_active: bool,
    irrigation_source: str = "Rainfed Only",
    language: str = "en"
) -> str:
    """
    Generate actionable agronomic recommendations and irrigation schedules in English or Telugu.
    
    Args:
        crop_name: Cultivated crop (e.g. 'Maize (Corn)', 'Groundnut (Peanut)', 'Sorghum').
        growth_stage: Crop phenological stage ('Seedling', 'Vegetative', 'Flowering', 'Harvest').
        drought_level: Assessed drought hazard ('Low', 'Moderate', 'High', 'Critical').
        soil_deficit_mm: Calculated rootzone water deficit in millimeters.
        heatwave_active: True if extreme temperature exceeds crop limit.
        irrigation_source: Irrigation mode ('Rainfed Only', 'Borewell', 'Drip System', etc.).
        language: Language code ('en' for English, 'te' for Telugu).
        
    Returns:
        JSON string containing immediate 24-48h interventions, 7-day irrigation directives,
        long-term resilience measures, a 2G SMS text alert, and safety disclaimers.
    """
    is_te = language.lower() in ["te", "telugu"]
    matched_crop = None
    clean_crop = crop_name.strip().lower()
    for c_name in CROP_DATABASE:
        if c_name.lower() == clean_crop:
            matched_crop = c_name
            break
    if not matched_crop:
        for c_name in CROP_DATABASE:
            if clean_crop in c_name.lower() or c_name.lower() in clean_crop:
                matched_crop = c_name
                break
    if not matched_crop:
        matched_crop = "Maize (Corn)"

    crop_info = CROP_DATABASE[matched_crop]
    immediate_en = []
    immediate_te = []

    # 1. Heatwave Actions
    if heatwave_active:
        immediate_en.append(
            "🔥 Thermal Stress: Irrigate strictly in late evening or night hours to prevent canopy scorching and evaporative loss."
        )
        immediate_te.append(
            f"🔥 అధిక ఉష్ణోగ్రత హెచ్చరిక: ఎండ తీవ్రత వల్ల తేమ ఆవిరి కాకుండా మరియు పంట మాడిపోకుండా ఉండటానికి సాయంత్రం లేదా రాత్రి వేళల్లో మాత్రమే తడులు ఇవ్వండి. ({TELUGU_COMMON_ADVICE['evening_irrigation']})"
        )
        if "flower" in growth_stage.lower() or "anthesis" in growth_stage.lower():
            immediate_en.append(
                "🌸 Anthesis Protection: Ensure rootzone moisture is maintained today to prevent pollen desiccation and flower drop."
            )
            immediate_te.append(
                f"🌸 పూత రక్షణ: పూత రాలిపోకుండా ఉండేందుకు వేర్ల వద్ద తేమను కాపాడండి. ({TELUGU_COMMON_ADVICE['pollen_protection']})"
            )

    # 2. Moisture Deficit & Drought Actions
    if drought_level in ["High", "Critical"] or soil_deficit_mm > 15.0:
        if irrigation_source != "Rainfed Only":
            immediate_en.append(
                f"💧 Deficit Irrigation: Soil deficit is {soil_deficit_mm:.1f} mm. Apply targeted rootzone micro-irrigation; avoid furrow flooding."
            )
            immediate_te.append(
                f"💧 పొదుపు నీటి తడులు: నేలలో {soil_deficit_mm:.1f} మి.మీ తేమ కొరత ఉంది. కాల్వల ద్వారా కాకుండా బిందు సేద్యం (డ్రిప్) ద్వారా నేరుగా వేర్లకే నీరందించండి."
            )
        else:
            immediate_en.append(
                "🍂 Immediate Mulching: Rainfed crop under moisture deficit. Spread 5-8 cm of dry biomass, straw, or leaves to seal in residual soil water."
            )
            immediate_te.append(
                f"🍂 ఆచ్ఛాదన (మల్చింగ్): వర్షాధార పంటలకు నేల తేమ ఆవిరి కాకుండా 5-8 సెం.మీ మేర ఎండు గడ్డి లేదా పంట వ్యర్థాలతో ఆచ్ఛాదన చేయండి. ({TELUGU_COMMON_ADVICE['mulching']})"
            )

    if not immediate_en:
        immediate_en.append("✅ Stable Conditions: Soil moisture and atmospheric conditions are within optimal parameters. Continue routine field scouting.")
        immediate_te.append("✅ అనుకూల పరిస్థితులు: నేల తేమ మరియు ఉష్ణోగ్రత అనుకూలంగా ఉన్నాయి. సాధారణ పంట సంరక్షణ చర్యలు కొనసాగించండి.")

    # 3. Long-term Resilience Practices
    resilience_en = list(crop_info["resilience_interventions"])
    resilience_te = [
        f"{TELUGU_CROPS.get(matched_crop, matched_crop)} పంటకు తగిన మేలైన యాజమాన్య పద్ధతులు పాటించండి.",
        TELUGU_COMMON_ADVICE["organic_manure"],
        TELUGU_COMMON_ADVICE["deficit_drip"],
        TELUGU_COMMON_ADVICE["drainage_trenches"]
    ]

    # 4. Low-Bandwidth 2G SMS / Audio Broadcast Card
    crop_lbl = TELUGU_CROPS.get(matched_crop, matched_crop) if is_te else matched_crop
    stage_lbl = TELUGU_STAGES.get(growth_stage, growth_stage) if is_te else growth_stage
    risk_lbl = TELUGU_RISK_LEVELS.get(drought_level, drought_level) if is_te else drought_level

    if is_te:
        sms = (
            f"🌾 ఫామ్‌గార్డ్ అలర్ట్ | {crop_lbl} ({stage_lbl})\n"
            f"కరువు ప్రమాద స్థాయి: {risk_lbl}\n"
            f"తక్షణ కర్తవ్యం:\n" + "\n".join([f"• {act}" for act in immediate_te[:2]]) +
            "\n- ఫామ్‌గార్డ్ ఏఐ (FarmGuard AI)"
        )
    else:
        sms = (
            f"🌾 FarmGuard Alert | {crop_lbl} ({stage_lbl})\n"
            f"Drought Risk Level: {risk_lbl}\n"
            f"Immediate Actions:\n" + "\n".join([f"• {act}" for act in immediate_en[:2]]) +
            "\n- FarmGuard AI Multi-Agent Engine"
        )

    disclaimer = get_safety_disclaimer(language)

    return json.dumps({
        "status": "success",
        "language": language,
        "crop_name": matched_crop,
        "growth_stage": growth_stage,
        "immediate_actions": immediate_te if is_te else immediate_en,
        "resilience_recommendations": resilience_te if is_te else resilience_en,
        "sms_dispatch": sms,
        "safety_disclaimer": disclaimer
    }, ensure_ascii=False)

