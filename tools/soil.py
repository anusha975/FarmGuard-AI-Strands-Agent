"""
Soil Moisture and Rootzone Hydrology Analysis Tool for FarmGuard AI.
Uses the official AWS Strands Agents SDK @tool decorator.
Calculates FAO-56 dual crop water balance, rootzone depletion, and Crop Water Stress Index (CWSI).
"""
import json
from strands import tool
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES

@tool
def analyze_soil_moisture(
    soil_type: str,
    crop_name: str,
    growth_stage: str,
    current_moisture_pct: float
) -> str:
    """
    Analyze soil water dynamics and crop moisture stress based on the FAO-56 standard.
    
    Args:
        soil_type: Soil texture (e.g. 'Sandy Loam', 'Clay / Black Cotton Soil (Vertisol)', 'Loam').
        crop_name: Cultivated crop (e.g. 'Maize (Corn)', 'Groundnut (Peanut)', 'Chickpea (Gram)', 'Sorghum').
        growth_stage: Phenological stage ('Germination/Seedling', 'Vegetative', 'Flowering/Anthesis', 'Grain Filling', 'Maturity').
        current_moisture_pct: Volumetric or estimated soil moisture percentage (0.0 to 100.0).
        
    Returns:
        JSON string containing TAW, RAW, depletion depth, transpiration stress factor Ks,
        CWSI (Crop Water Stress Index), transparent risk level, and agronomic explanations.
    """
    # 1. Input Validation
    if not isinstance(current_moisture_pct, (int, float)) or not (0.0 <= current_moisture_pct <= 100.0):
        return json.dumps({
            "status": "error",
            "error_type": "ValidationError",
            "message": f"Invalid current_moisture_pct: {current_moisture_pct}. Must be between 0.0% and 100.0%."
        })

    # Normalize soil and crop lookups
    matched_soil = None
    for s_name in SOIL_PROPERTIES:
        if s_name.lower() in soil_type.lower() or soil_type.lower() in s_name.lower():
            matched_soil = s_name
            break
    if not matched_soil:
        matched_soil = "Loam"  # Sensible agricultural fallback with notice

    matched_crop = None
    for c_name in CROP_DATABASE:
        if c_name.lower() in crop_name.lower() or crop_name.lower() in c_name.lower():
            matched_crop = c_name
            break
    if not matched_crop:
        matched_crop = "Maize (Corn)"

    crop_info = CROP_DATABASE[matched_crop]
    soil_info = SOIL_PROPERTIES[matched_soil]

    fc_pct = soil_info["field_capacity_pct"]
    pwp_pct = soil_info["permanent_wilting_point_pct"]
    fc = fc_pct / 100.0
    pwp = pwp_pct / 100.0
    current_sm = current_moisture_pct / 100.0

    # 2. Rooting Depth (Zr) by Growth Stage
    stage_lower = growth_stage.lower()
    if "seedling" in stage_lower or "germination" in stage_lower:
        zr = crop_info["rooting_depth_m"]["initial"]
    elif "maturity" in stage_lower or "harvest" in stage_lower:
        zr = crop_info["rooting_depth_m"]["max"]
    else:
        zr = crop_info["rooting_depth_m"]["mid"]

    p = crop_info["depletion_fraction_p"]

    # 3. FAO-56 Hydrology Calculations
    # TAW = 1000 * (FC - PWP) * Zr (mm)
    taw_mm = 1000.0 * (fc - pwp) * zr
    # RAW = p * TAW (mm)
    raw_mm = p * taw_mm

    # Current storage above wilting point (mm)
    current_storage_mm = max(0.0, 1000.0 * (current_sm - pwp) * zr)
    # Rootzone depletion Dr (mm)
    depletion_mm = max(0.0, taw_mm - current_storage_mm)

    # Transpiration reduction factor Ks (FAO-56 Eq. 84)
    # If Dr <= RAW, Ks = 1.0 (no water stress)
    # If Dr > RAW, Ks = (TAW - Dr) / ((1 - p) * TAW)
    if depletion_mm <= raw_mm:
        ks = 1.0
        cwsi = 0.0
        risk_level = "Low"
        reason = (
            f"Soil moisture ({current_moisture_pct:.1f}%) is within the Readily Available Water buffer "
            f"({raw_mm:.1f}mm). Crop can extract water easily without stomatal closure."
        )
        irrigation_needed_mm = 0.0
    else:
        denom = max(0.001, (1.0 - p) * taw_mm)
        ks = max(0.0, min(1.0, (taw_mm - depletion_mm) / denom))
        cwsi = round(1.0 - ks, 2)
        irrigation_needed_mm = round(depletion_mm, 1)

        if current_moisture_pct <= pwp_pct:
            risk_level = "Critical"
            reason = (
                f"CRITICAL WILTING HAZARD: Moisture ({current_moisture_pct:.1f}%) is at or below Permanent Wilting Point "
                f"({pwp_pct}%). Soil suction exceeds root pulling tension; plant cells lose turgor and risk permanent cavitation."
            )
        elif cwsi >= 0.5:
            risk_level = "High"
            reason = (
                f"HIGH WATER DEFICIT: Rootzone depletion ({depletion_mm:.1f}mm) exceeds safety buffer ({raw_mm:.1f}mm). "
                f"Crop transpiration is curtailed by {int(cwsi * 100)}%, restricting photosynthesis."
            )
        else:
            risk_level = "Moderate"
            reason = (
                f"MODERATE MOISTURE PINCH: Rootzone depletion ({depletion_mm:.1f}mm) has just crossed the depletion threshold "
                f"({raw_mm:.1f}mm). Light vegetative slowing expected."
            )

    return json.dumps({
        "status": "success",
        "crop_name": matched_crop,
        "soil_type": matched_soil,
        "growth_stage": growth_stage,
        "effective_root_depth_m": zr,
        "field_capacity_pct": fc_pct,
        "permanent_wilting_point_pct": pwp_pct,
        "current_moisture_pct": round(current_moisture_pct, 1),
        "total_available_water_taw_mm": round(taw_mm, 1),
        "readily_available_water_raw_mm": round(raw_mm, 1),
        "rootzone_depletion_mm": round(depletion_mm, 1),
        "transpiration_factor_ks": round(ks, 2),
        "crop_water_stress_index_cwsi": cwsi,
        "soil_risk_level": risk_level,
        "irrigation_needed_mm": irrigation_needed_mm,
        "agronomic_reason": reason,
        "soil_management_tip": soil_info["management_tip"]
    })
