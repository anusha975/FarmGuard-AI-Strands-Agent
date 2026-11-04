"""
Drought, Heatwave, and Extreme Climate Risk Assessment Tool for FarmGuard AI.
Decorated with @tool for direct execution by the AWS Strands Agent.
"""
import json
from strands import tool
from farmguard.data.crop_knowledge import CROP_DATABASE
from farmguard.utils.logger import logger

@tool
def assess_drought_risk(
    rainfall_7d_mm: float,
    et0_7d_mm: float,
    dry_days: int,
    max_forecast_temp_c: float,
    crop_name: str,
    growth_stage: str
) -> str:
    """
    Assess meteorological drought deficit, thermal heatwave anomaly, and extreme weather risk.
    
    Args:
        rainfall_7d_mm: Cumulative 7-day precipitation in mm
        et0_7d_mm: Cumulative 7-day FAO-56 reference evapotranspiration in mm
        dry_days: Number of consecutive days with precipitation < 1.0mm
        max_forecast_temp_c: Highest predicted temperature in Celsius
        crop_name: Cultivated crop name
        growth_stage: Current crop growth stage
        
    Returns:
        JSON string containing drought severity score (0-100), heatwave severity score,
        flood hazard score, and prioritized hazard classification.
    """
    logger.info(f"[Tool: assess_drought_risk] Calculating hazards for {crop_name} (Rain={rainfall_7d_mm}mm, ET0={et0_7d_mm}mm)")
    
    crop_info = CROP_DATABASE.get(crop_name, CROP_DATABASE["Maize (Corn)"])
    crit_temp = crop_info["critical_temp_max_c"]
    
    # 1. Drought Balance (Precipitation - ET0)
    net_balance = rainfall_7d_mm - et0_7d_mm
    drought_score = 0.0
    
    if net_balance < -25.0:
        drought_score += 50.0
    elif net_balance < -10.0:
        drought_score += 30.0
    elif net_balance < 0.0:
        drought_score += 15.0
        
    if dry_days >= 6:
        drought_score += 35.0
    elif dry_days >= 4:
        drought_score += 20.0
    elif dry_days >= 2:
        drought_score += 10.0
        
    # Flowering/Anthesis phase doubles drought sensitivity
    is_flowering = "flower" in growth_stage.lower() or "anthesis" in growth_stage.lower()
    if is_flowering:
        drought_score = min(100.0, drought_score * 1.25)
        
    # Crop drought tolerance discount
    if crop_info["drought_tolerance"] == "Very High":
        drought_score = max(0.0, drought_score * 0.70)
    elif crop_info["drought_tolerance"] == "High":
        drought_score = max(0.0, drought_score * 0.85)
        
    drought_score = round(min(100.0, max(0.0, drought_score)), 1)
    drought_level = "Critical" if drought_score >= 70 else "High" if drought_score >= 45 else "Moderate" if drought_score >= 25 else "Low"
    
    # 2. Heatwave Severity
    heat_score = 0.0
    if max_forecast_temp_c >= crit_temp + 3.0:
        heat_score = 90.0
    elif max_forecast_temp_c >= crit_temp:
        heat_score = 70.0
    elif max_forecast_temp_c >= crit_temp - 2.0:
        heat_score = 45.0
    else:
        heat_score = 15.0
        
    if is_flowering and max_forecast_temp_c >= crit_temp:
        heat_score = min(100.0, heat_score + 15.0)
        
    heat_level = "Critical" if heat_score >= 70 else "High" if heat_score >= 45 else "Moderate" if heat_score >= 25 else "Low"
    
    # 3. Flood / Excessive Rain Hazard
    flood_score = 0.0
    if rainfall_7d_mm > 100.0:
        flood_score = 85.0
    elif rainfall_7d_mm > 60.0:
        flood_score = 55.0
    elif rainfall_7d_mm > 30.0:
        flood_score = 25.0
    else:
        flood_score = 5.0
    flood_level = "Critical" if flood_score >= 70 else "High" if flood_score >= 45 else "Moderate" if flood_score >= 25 else "Low"
    
    # Composite vulnerability index
    composite_cvi = round(0.40 * drought_score + 0.35 * heat_score + 0.25 * flood_score, 1)
    
    result = {
        "status": "success",
        "crop_evaluated": crop_name,
        "critical_temperature_limit_c": crit_temp,
        "drought_score_pct": drought_score,
        "drought_level": drought_level,
        "heatwave_score_pct": heat_score,
        "heatwave_level": heat_level,
        "flood_score_pct": flood_score,
        "flood_level": flood_level,
        "composite_vulnerability_index": composite_cvi,
        "primary_hazard": "Drought" if drought_score >= max(heat_score, flood_score) else "Heatwave" if heat_score >= flood_score else "Heavy Rain"
    }
    return json.dumps(result)
