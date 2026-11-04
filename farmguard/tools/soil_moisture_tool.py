"""
Soil moisture deficit, water balance, and Crop Water Stress Index (CWSI) computation.
Follows the FAO-56 (Food and Agriculture Organization) dual crop coefficient standard.
"""
from typing import Dict, Any
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES
from farmguard.models import RiskMetric

def analyze_soil_moisture_stress(
    crop_name: str,
    growth_stage: str,
    soil_type: str,
    current_soil_moisture_pct: float
) -> Dict[str, Any]:
    """
    Compute agronomic soil water balance, depletion status, and crop water stress.
    
    FAO-56 formulation:
      TAW (Total Available Water in mm) = 1000 * (FC - PWP) * Zr
      RAW (Readily Available Water in mm) = p * TAW
      Dr (Root zone depletion in mm)
      Ks (Transpiration reduction factor, 0.0 to 1.0)
    """
    crop_info = CROP_DATABASE.get(crop_name, CROP_DATABASE["Maize (Corn)"])
    soil_info = SOIL_PROPERTIES.get(soil_type, SOIL_PROPERTIES["Loam"])
    
    fc = soil_info["field_capacity_pct"] / 100.0
    pwp = soil_info["permanent_wilting_point_pct"] / 100.0
    current_sm = current_soil_moisture_pct / 100.0
    
    # Determine effective root depth (Zr)
    stage_key = growth_stage.lower()
    if "seedling" in stage_key or "germination" in stage_key:
        zr = crop_info["rooting_depth_m"]["initial"]
    elif "maturity" in stage_key or "harvest" in stage_key:
        zr = crop_info["rooting_depth_m"]["max"]
    else:
        zr = crop_info["rooting_depth_m"]["mid"]
        
    p = crop_info["depletion_fraction_p"]
    
    # TAW in mm
    taw_mm = 1000.0 * (fc - pwp) * zr
    # RAW in mm
    raw_mm = p * taw_mm
    
    # Current available water in mm
    current_storage_mm = max(0.0, 1000.0 * (current_sm - pwp) * zr)
    # Soil water depletion (Dr)
    depletion_mm = max(0.0, taw_mm - current_storage_mm)
    
    # Crop water stress factor Ks (FAO-56 Eq. 84)
    # If Dr <= RAW: Ks = 1.0 (no water stress)
    # If Dr > RAW: Ks = (TAW - Dr) / ((1 - p) * TAW)
    if depletion_mm <= raw_mm:
        ks = 1.0
        stress_level = "None to Minimal"
        score_pct = 15.0
    else:
        denom = max(0.001, (1.0 - p) * taw_mm)
        ks = max(0.0, min(1.0, (taw_mm - depletion_mm) / denom))
        # Stress increases as Ks drops
        score_pct = (1.0 - ks) * 100.0
        if score_pct > 75.0:
            stress_level = "Critical"
        elif score_pct > 50.0:
            stress_level = "High"
        else:
            stress_level = "Moderate"
            
    # Crop Water Stress Index (CWSI ~ 1 - Ks)
    cwsi = round(1.0 - ks, 2)
    
    # Determine risk level
    if current_soil_moisture_pct <= soil_info["permanent_wilting_point_pct"]:
        risk_level = "Critical"
        score_pct = 95.0
        impact = f"Soil moisture ({current_soil_moisture_pct:.1f}%) is at or below Permanent Wilting Point ({soil_info['permanent_wilting_point_pct']}%). Severe root cavitation and irreversible yield penalty occurring."
    elif depletion_mm > raw_mm:
        risk_level = "High" if score_pct >= 60 else "Moderate"
        impact = f"Depletion ({depletion_mm:.1f}mm) has breached the crop readily available water threshold ({raw_mm:.1f}mm). Transpiration is reduced by {(1-ks)*100:.0f}%."
    else:
        risk_level = "Low"
        impact = f"Soil moisture is in the readily available buffer zone. No immediate water deficit stress detected."
        
    metric = RiskMetric(
        category="Soil Moisture Stress",
        score_pct=round(score_pct, 1),
        risk_level=risk_level,
        primary_driver=f"Rootzone moisture ({current_soil_moisture_pct:.1f}%) vs Field Capacity ({soil_info['field_capacity_pct']}%)",
        impact_explanation=impact,
        alert_triggered=(risk_level in ["High", "Critical"])
    )
    
    return {
        "metric": metric,
        "taw_mm": round(taw_mm, 1),
        "raw_mm": round(raw_mm, 1),
        "depletion_mm": round(depletion_mm, 1),
        "ks_transpiration_factor": round(ks, 2),
        "cwsi": cwsi,
        "irrigation_needed_mm": round(depletion_mm, 1) if depletion_mm > raw_mm else 0.0,
        "soil_management_tip": soil_info["management_tip"]
    }
