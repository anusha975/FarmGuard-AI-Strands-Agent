"""
Bilingual Farming Recommendations & Actionable Adaptation Tool for FarmGuard AI.
Decorated with @tool for direct execution by the AWS Strands Agent.
Supports English and Telugu (తెలుగు) localization.
"""
import json
from strands import tool
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES
from farmguard.data.telugu_translations import (
    TELUGU_CROPS,
    TELUGU_STAGES,
    TELUGU_RISK_LEVELS,
    TELUGU_COMMON_ADVICE
)
from farmguard.utils.logger import logger

@tool
def generate_farming_recommendations(
    crop_name: str,
    growth_stage: str,
    drought_level: str,
    soil_deficit_mm: float,
    heatwave_active: bool,
    irrigation_source: str = "Rainfed Only",
    language: str = "en"
) -> str:
    """
    Generate bilingual actionable farming recommendations, immediate tactical interventions,
    and deficit irrigation guidance in English and Telugu.
    
    Args:
        crop_name: Cultivated crop name
        growth_stage: Crop development stage
        drought_level: Assessed drought level ('Low', 'Moderate', 'High', 'Critical')
        soil_deficit_mm: Water deficit depth in millimeters
        heatwave_active: Boolean indicating if extreme temperatures are forecast
        irrigation_source: Water access mode ('Rainfed Only', 'Borewell', 'Drip System', etc.)
        language: Language preference ('en' for English, 'te' for Telugu)
        
    Returns:
        JSON string containing immediate_actions, 7-day guidance principles,
        long_term_resilience tips, and a formatted 2G SMS alert.
    """
    logger.info(f"[Tool: generate_farming_recommendations] Synthesizing recommendations in '{language}' for {crop_name}")
    
    is_te = language.lower() in ["te", "telugu"]
    crop_info = CROP_DATABASE.get(crop_name, CROP_DATABASE["Maize (Corn)"])
    
    immediate_en = []
    immediate_te = []
    
    # 1. Heatwave Actions
    if heatwave_active:
        immediate_en.append(
            "🔥 Extreme Thermal Stress: Restrict irrigation strictly to late evening or night hours to reduce evaporation and prevent canopy scalding."
        )
        immediate_te.append(
            f"🔥 ఎండ తీవ్రత అధికంగా ఉంది: నీటి ఆవిరిని తగ్గించడానికి మరియు పంట కమిలిపోకుండా ఉండటానికి కేవలం సాయంత్రం లేదా రాత్రి వేళల్లో మాత్రమే తడులు ఇవ్వండి. ({TELUGU_COMMON_ADVICE['evening_irrigation']})"
        )
        if "flower" in growth_stage.lower() or "anthesis" in growth_stage.lower():
            immediate_en.append(
                "🌸 Anthesis Protection: Maintain protective rootzone moisture today to safeguard pollen viability and prevent flower abortion."
            )
            immediate_te.append(
                f"🌸 పూత రక్షణ: పూత రాలిపోకుండా ఉండేందుకు వేర్ల వద్ద తగినంత తేమ ఉండేలా చూడండి. ({TELUGU_COMMON_ADVICE['pollen_protection']})"
            )

    # 2. Drought & Soil Deficit Actions
    if drought_level in ["High", "Critical"] or soil_deficit_mm > 15.0:
        if irrigation_source != "Rainfed Only":
            immediate_en.append(
                f"💧 Deficit Irrigation: Soil deficit is {soil_deficit_mm:.1f} mm. Apply targeted micro-irrigation at the root zone rather than flood irrigation."
            )
            immediate_te.append(
                f"💧 పొదుపు నీటి యాజమాన్యం: నేలలో {soil_deficit_mm:.1f} మి.మీ తేమ కొరత ఉంది. నేరుగా కాలువల ద్వారా కాకుండా బిందు సేద్యం (డ్రిప్) ద్వారా నేరుగా వేర్లకే నీరందించండి."
            )
        else:
            immediate_en.append(
                "🍂 Emergency Organic Mulch: Rainfed crop detected under water stress. Spread 5-8 cm of crop residue, straw, or dry biomass to trap residual moisture."
            )
            immediate_te.append(
                f"🍂 ఆచ్ఛాదన (మల్చింగ్): వర్షాధార పంటలకు నీటి ఎద్దడి రాకుండా 5-8 సెం.మీ మేర ఎండు గడ్డి లేదా పంట వ్యర్థాలతో ఆచ్ఛాదన చేయండి. ({TELUGU_COMMON_ADVICE['mulching']})"
            )
            
    if not immediate_en:
        immediate_en.append("✅ Favorable Conditions: Soil moisture and temperature are within safe agronomic parameters. Continue routine weeding.")
        immediate_te.append("✅ అనుకూల పరిస్థితులు: నేల తేమ మరియు వాతావరణం అనుకూలంగా ఉన్నాయి. సాధారణ కలుపు తీత కొనసాగించండి.")

    # Resilience Interventions
    resilience_en = list(crop_info["resilience_interventions"])
    resilience_te = [
        f"{TELUGU_CROPS.get(crop_name, crop_name)} పంటకు తగిన మేలైన యాజమాన్య పద్ధతులు పాటించండి.",
        TELUGU_COMMON_ADVICE["organic_manure"],
        TELUGU_COMMON_ADVICE["deficit_drip"]
    ]
    
    # SMS Format
    crop_display = TELUGU_CROPS.get(crop_name, crop_name) if is_te else crop_name
    stage_display = TELUGU_STAGES.get(growth_stage, growth_stage) if is_te else growth_stage
    level_display = TELUGU_RISK_LEVELS.get(drought_level, drought_level) if is_te else drought_level
    
    if is_te:
        sms = (
            f"🌾 ఫామ్‌గార్డ్ అలర్ట్ | {crop_display} ({stage_display})\n"
            f"కరువు ప్రమాద స్థాయి: {level_display}\n"
            f"తక్షణ కర్తవ్యం:\n" + "\n".join([f"• {act}" for act in immediate_te[:2]]) +
            "\n- ఫామ్‌గార్డ్ ఏఐ (FarmGuard AI)"
        )
    else:
        sms = (
            f"🌾 FarmGuard Alert | {crop_display} ({stage_display})\n"
            f"Drought Risk Level: {level_display}\n"
            f"Immediate Actions:\n" + "\n".join([f"• {act}" for act in immediate_en[:2]]) +
            "\n- FarmGuard AI Multi-Agent Engine"
        )
        
    result = {
        "language_selected": language,
        "crop_name": crop_name,
        "growth_stage": growth_stage,
        "immediate_actions": immediate_te if is_te else immediate_en,
        "resilience_recommendations": resilience_te if is_te else resilience_en,
        "sms_dispatch": sms
    }
    return json.dumps(result, ensure_ascii=False)
