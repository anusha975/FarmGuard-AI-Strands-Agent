"""
Soil Moisture and Rootzone Hydrology Analysis Tool for FarmGuard AI.
Decorated with @tool for direct execution by the AWS Strands Agent.
"""
import json
from strands import tool
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES
from farmguard.utils.logger import logger

@tool
def analyze_soil(
    soil_type: str,
    crop_name: str,
    growth_stage: str,
    current_soil_moisture_pct: float
) -> str:
    """
    Compute FAO-56 rootzone water balance, readily available water buffer, and Crop Water Stress Index.
    
    Args:
        soil_type: Soil texture (e.g. 'Sandy Loam', 'Clay / Black Cotton Soil (Vertisol)', 'Loam')
        crop_name: Cultivated crop name (e.g. 'Maize (Corn)', 'Groundnut (Peanut)', 'Chickpea (Gram)')
        growth_stage: Current stage ('Germination/Seedling', 'Vegetative', 'Flowering/Anthesis', 'Grain Filling/Tuber Bulking', 'Maturity/Harvest')
        current_soil_moisture_pct: Measured or modeled soil moisture percentage (0.0 to 100.0)
        
    Returns:
        JSON string containing TAW, RAW, depletion_mm, CWSI (Crop Water Stress Index),
        water deficit status, and irrigation requirement in millimeters.
    """
    logger.info(f"[Tool: analyze_soil] Evaluating {crop_name} in {soil_type} at {current_soil_moisture_pct:.1f}% moisture")
    
    crop_info = CROP_DATABASE.get(crop_name, CROP_DATABASE["Maize (Corn)"])
    soil_info = SOIL_PROPERTIES.get(soil_type, SOIL_PROPERTIES["Loam"])
    
    fc = soil_info["field_capacity_pct"] / 100.0
    pwp = soil_info["permanent_wilting_point_pct"] / 100.0
    current_sm = current_soil_moisture_pct / 100.0
    
    # Rooting depth Zr (meters)
    stage_key = growth_stage.lower()
    if "seedling" in stage_key or "germination" in stage_key:
        zr = crop_info["rooting_depth_m"]["initial"]
    elif "maturity" in stage_key or "harvest" in stage_key:
        zr = crop_info["rooting_depth_m"]["max"]
    else:
        zr = crop_info["rooting_depth_m"]["mid"]
        
    p = crop_info["depletion_fraction_p"]
    
    # Total Available Water (TAW) & Readily Available Water (RAW) in mm
    taw_mm = 1000.0 * (fc - pwp) * zr
    raw_mm = p * taw_mm
    
    # Current water storage & depletion Dr in mm
    current_storage_mm = max(0.0, 1000.0 * (current_sm - pwp) * zr)
    depletion_mm = max(0.0, taw_mm - current_storage_mm)
    
    # Transpiration reduction factor Ks (FAO-56)
    if depletion_mm <= raw_mm:
        ks = 1.0
        cwsi = 0.0
        stress_level = "None"
        irrigation_needed_mm = 0.0
    else:
        denom = max(0.001, (1.0 - p) * taw_mm)
        ks = max(0.0, min(1.0, (taw_mm - depletion_mm) / denom))
        cwsi = round(1.0 - ks, 2)
        stress_level = "Critical" if cwsi >= 0.6 else "High" if cwsi >= 0.35 else "Moderate"
        irrigation_needed_mm = round(depletion_mm, 1)
        
    if current_soil_moisture_pct <= soil_info["permanent_wilting_point_pct"]:
        status = "CRITICAL_WILTING_POINT_BREACHED"
        desc = f"Soil moisture ({current_soil_moisture_pct:.1f}%) is at or below Permanent Wilting Point ({soil_info['permanent_wilting_point_pct']}%). Root uptake ceases."
    elif depletion_mm > raw_mm:
        status = "MOISTURE_DEFICIT_STRESS"
        desc = f"Rootzone moisture has breached readily available threshold ({raw_mm:.1f}mm buffer). Crop transpiration is reduced by {int(cwsi * 100)}%."
    else:
        status = "OPTIMAL_WATER_BUFFER"
        desc = "Rootzone moisture is in the optimal buffer zone. Crop is transpiring without deficit stress."
        
    result = {
        "status": status,
        "is_simulated": False,
        "data_source": "🟢 SCIENTIFIC HYDROLOGY (FAO-56 Dual Crop Water Balance)",
        "crop_name": crop_name,
        "soil_type": soil_type,
        "effective_root_depth_m": zr,
        "field_capacity_pct": soil_info["field_capacity_pct"],
        "permanent_wilting_point_pct": soil_info["permanent_wilting_point_pct"],
        "current_moisture_pct": round(current_soil_moisture_pct, 1),
        "total_available_water_taw_mm": round(taw_mm, 1),
        "readily_available_water_raw_mm": round(raw_mm, 1),
        "rootzone_depletion_mm": round(depletion_mm, 1),
        "transpiration_factor_ks": round(ks, 2),
        "crop_water_stress_index_cwsi": cwsi,
        "stress_level": stress_level,
        "irrigation_needed_mm": irrigation_needed_mm,
        "soil_management_tip": soil_info["management_tip"],
        "explanation": desc
    }
    return json.dumps(result)
