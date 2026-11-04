"""
Drought Risk and Extreme Climate Hazard Assessment Tool for FarmGuard AI.
Uses the official AWS Strands Agents SDK @tool decorator.
Evaluates meteorological deficit, evaporative atmospheric demand, and phenological sensitivity.
"""
import json
from strands import tool
from farmguard.data.crop_knowledge import CROP_DATABASE

@tool
def calculate_drought_risk(
    rainfall_7d_mm: float,
    et0_7d_mm: float,
    dry_days: int,
    max_temp_c: float,
    crop_name: str,
    growth_stage: str
) -> str:
    """
    Compute meteorological drought deficit, thermal heatwave anomaly, and composite risk levels.
    
    Args:
        rainfall_7d_mm: Cumulative 7-day rainfall in millimeters (>= 0.0).
        et0_7d_mm: Cumulative 7-day FAO-56 reference evapotranspiration in millimeters (>= 0.0).
        dry_days: Number of consecutive days with precipitation < 1.0mm (0 to 7).
        max_temp_c: Highest predicted temperature in Celsius.
        crop_name: Cultivated crop name.
        growth_stage: Current crop growth stage.
        
    Returns:
        JSON string containing drought score, drought risk level, heatwave risk level,
        flood risk level, and transparent causal explanations for each rating.
    """
    # 1. Input Validation
    if rainfall_7d_mm < 0.0:
        return json.dumps({"status": "error", "error_type": "ValidationError", "message": f"Rainfall cannot be negative: {rainfall_7d_mm}"})
    if et0_7d_mm < 0.0:
        return json.dumps({"status": "error", "error_type": "ValidationError", "message": f"ET0 cannot be negative: {et0_7d_mm}"})
    if dry_days < 0 or dry_days > 7:
        return json.dumps({"status": "error", "error_type": "ValidationError", "message": f"dry_days must be between 0 and 7, got: {dry_days}"})

    matched_crop = None
    for c_name in CROP_DATABASE:
        if c_name.lower() in crop_name.lower() or crop_name.lower() in c_name.lower():
            matched_crop = c_name
            break
    if not matched_crop:
        matched_crop = "Maize (Corn)"

    crop_info = CROP_DATABASE[matched_crop]
    crit_temp = crop_info["critical_temp_max_c"]

    # 2. Net Water Deficit Calculation
    net_balance = rainfall_7d_mm - et0_7d_mm
    drought_score = 0.0
    drivers = []

    if net_balance < -25.0:
        drought_score += 45.0
        drivers.append(f"Severe atmospheric deficit (Rainfall {rainfall_7d_mm:.1f}mm vs ET0 {et0_7d_mm:.1f}mm = {net_balance:.1f}mm)")
    elif net_balance < -10.0:
        drought_score += 25.0
        drivers.append(f"Moderate negative moisture balance ({net_balance:.1f}mm)")
    elif net_balance < 0.0:
        drought_score += 15.0
        drivers.append(f"Mild moisture deficit ({net_balance:.1f}mm)")

    if dry_days >= 6:
        drought_score += 35.0
        drivers.append(f"Prolonged dry streak of {dry_days} consecutive days")
    elif dry_days >= 4:
        drought_score += 20.0
        drivers.append(f"Dry streak of {dry_days} days without meaningful precipitation")
    elif dry_days >= 2:
        drought_score += 10.0

    is_flowering = "flower" in growth_stage.lower() or "anthesis" in growth_stage.lower()
    if is_flowering:
        drought_score = min(100.0, drought_score * 1.25)
        drivers.append("Crop is in flowering/anthesis phase (25% higher drought vulnerability)")

    # Drought tolerance factor
    if crop_info["drought_tolerance"] == "Very High":
        drought_score = max(0.0, drought_score * 0.70)
        drivers.append(f"{matched_crop} has high native drought resilience (30% score discount applied)")
    elif crop_info["drought_tolerance"] == "High":
        drought_score = max(0.0, drought_score * 0.85)

    drought_score = round(min(100.0, max(0.0, drought_score)), 1)
    if drought_score >= 70:
        d_level = "Critical"
    elif drought_score >= 45:
        d_level = "High"
    elif drought_score >= 25:
        d_level = "Moderate"
    else:
        d_level = "Low"

    # 3. Heatwave Evaluation
    heat_score = 0.0
    heat_drivers = []
    if max_temp_c >= crit_temp + 3.0:
        heat_score = 90.0
        heat_drivers.append(f"Peak temperature {max_temp_c}°C substantially breaches crop threshold ({crit_temp}°C)")
    elif max_temp_c >= crit_temp:
        heat_score = 70.0
        heat_drivers.append(f"Peak temperature {max_temp_c}°C meets or exceeds crop thermal limit ({crit_temp}°C)")
    elif max_temp_c >= crit_temp - 2.0:
        heat_score = 40.0
        heat_drivers.append(f"Peak temperature {max_temp_c}°C is near thermal limit ({crit_temp}°C)")
    else:
        heat_score = 15.0
        heat_drivers.append(f"Temperature is within optimal agronomic range ({crop_info['optimal_temp_range'][0]}-{crop_info['optimal_temp_range'][1]}°C)")

    if is_flowering and max_temp_c >= crit_temp:
        heat_score = min(100.0, heat_score + 15.0)
        heat_drivers.append("Heatwave during anthesis threatens pollen viability and seed set")

    heat_score = round(min(100.0, max(0.0, heat_score)), 1)
    h_level = "Critical" if heat_score >= 70 else "High" if heat_score >= 45 else "Moderate" if heat_score >= 25 else "Low"

    # 4. Flood Risk
    flood_score = 85.0 if rainfall_7d_mm > 100.0 else 50.0 if rainfall_7d_mm > 60.0 else 20.0 if rainfall_7d_mm > 25.0 else 5.0
    f_level = "Critical" if flood_score >= 70 else "High" if flood_score >= 45 else "Moderate" if flood_score >= 25 else "Low"

    return json.dumps({
        "status": "success",
        "crop_name": matched_crop,
        "growth_stage": growth_stage,
        "net_water_balance_mm": round(net_balance, 1),
        "drought_score_pct": drought_score,
        "drought_risk_level": d_level,
        "drought_drivers": drivers,
        "heatwave_score_pct": heat_score,
        "heatwave_risk_level": h_level,
        "heatwave_drivers": heat_drivers,
        "flood_score_pct": flood_score,
        "flood_risk_level": f_level,
        "composite_vulnerability_index": round(0.40 * drought_score + 0.35 * heat_score + 0.25 * flood_score, 1)
    })

