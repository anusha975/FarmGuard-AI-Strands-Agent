"""
Drought, Heatwave, and Extreme Climate Risk calculation tools for FarmGuard AI.
Evaluates meteorological drought, atmospheric evaporative deficit, and heat stress.
"""
from typing import Dict, Any, Tuple
from farmguard.data.crop_knowledge import CROP_DATABASE
from farmguard.models import AgroWeatherData, RiskMetric

def calculate_climate_risks(
    weather: AgroWeatherData,
    crop_name: str,
    growth_stage: str
) -> Tuple[RiskMetric, RiskMetric, RiskMetric]:
    """
    Evaluate 3 distinct climate hazards:
    1. Meteorological / Hydrological Drought Risk
    2. Heatwave & Thermal Stress Risk
    3. Excessive Rainfall / Waterlogging / Flood Risk
    
    Returns: (drought_metric, heatwave_metric, flood_metric)
    """
    crop_info = CROP_DATABASE.get(crop_name, CROP_DATABASE["Maize (Corn)"])
    
    # ---------------- 1. Drought Risk Calculation ----------------
    # Net water balance = Precipitation - ET0
    net_water_balance = weather.total_precipitation_7d_mm - weather.total_et0_7d_mm
    dry_days = weather.consecutive_dry_days
    
    # Base drought scoring
    # If ET0 is 35mm and Rain is 0mm, deficit is -35mm
    drought_score = 0.0
    if net_water_balance < -25.0:
        drought_score += 45.0
    elif net_water_balance < -10.0:
        drought_score += 25.0
    elif net_water_balance < 0.0:
        drought_score += 15.0
        
    # Consecutive dry days weight
    if dry_days >= 6:
        drought_score += 35.0
    elif dry_days >= 4:
        drought_score += 20.0
    elif dry_days >= 2:
        drought_score += 10.0
        
    # Stage sensitivity modifier (Flowering/Anthesis is double sensitive)
    is_flowering = "flower" in growth_stage.lower() or "anthesis" in growth_stage.lower()
    if is_flowering:
        drought_score = min(100.0, drought_score * 1.25)
        
    # Crop inherent tolerance discount
    if crop_info["drought_tolerance"] == "Very High":
        drought_score = max(0.0, drought_score * 0.70)
    elif crop_info["drought_tolerance"] == "High":
        drought_score = max(0.0, drought_score * 0.85)
        
    drought_score = round(min(100.0, max(0.0, drought_score)), 1)
    
    if drought_score >= 70:
        d_level = "Critical"
        d_impact = f"Severe moisture deficit (Net Balance: {net_water_balance:.1f}mm, {dry_days} dry days). Crop will suffer permanent stunting or yield collapse without immediate intervention."
    elif drought_score >= 45:
        d_level = "High"
        d_impact = f"Moderate-to-high drought stress. Evapotranspiration ({weather.total_et0_7d_mm:.1f}mm) outstrips precipitation ({weather.total_precipitation_7d_mm:.1f}mm)."
    elif drought_score >= 25:
        d_level = "Moderate"
        d_impact = "Mild drying trend. Soil moisture buffer currently preventing acute wilt, but vigilance is required."
    else:
        d_level = "Low"
        d_impact = "Adequate precipitation or low evaporative demand. Low drought hazard for the upcoming 7 days."
        
    drought_metric = RiskMetric(
        category="Drought Risk",
        score_pct=drought_score,
        risk_level=d_level,
        primary_driver=f"7-day Net Water Deficit of {abs(net_water_balance):.1f}mm with {dry_days} dry days",
        impact_explanation=d_impact,
        alert_triggered=(d_level in ["High", "Critical"])
    )
    
    # ---------------- 2. Heatwave & Thermal Stress Calculation ----------------
    crit_temp = crop_info["critical_temp_max_c"]
    max_forecast = weather.max_forecast_temp_c
    heat_days = weather.heatwave_days_count
    
    heat_score = 0.0
    if max_forecast >= crit_temp + 3.0:
        heat_score += 55.0
    elif max_forecast >= crit_temp:
        heat_score += 40.0
    elif max_forecast >= crit_temp - 2.0:
        heat_score += 20.0
        
    heat_score += min(45.0, heat_days * 12.0)
    
    if is_flowering and max_forecast >= crit_temp:
        heat_score = min(100.0, heat_score + 15.0)
        
    heat_score = round(min(100.0, max(0.0, heat_score)), 1)
    
    if heat_score >= 70:
        h_level = "Critical"
        h_impact = f"Extreme thermal anomaly: {heat_days} days exceeding critical threshold ({crit_temp}°C). Risk of pollen abortion, scorching, and rapid desiccation."
    elif heat_score >= 45:
        h_level = "High"
        h_impact = f"Elevated heat stress forecast reaching {max_forecast}°C. High vapor pressure deficit will accelerate moisture loss."
    elif heat_score >= 20:
        h_level = "Moderate"
        h_impact = "Warm daytime conditions, manageable with adequate rootzone moisture."
    else:
        h_level = "Low"
        h_impact = f"Temperatures remain within optimal agronomic range ({crop_info['optimal_temp_range'][0]}-{crop_info['optimal_temp_range'][1]}°C)."
        
    heatwave_metric = RiskMetric(
        category="Heatwave & Thermal Stress",
        score_pct=heat_score,
        risk_level=h_level,
        primary_driver=f"Peak temperature {max_forecast}°C vs crop threshold {crit_temp}°C ({heat_days} heatwave days)",
        impact_explanation=h_impact,
        alert_triggered=(h_level in ["High", "Critical"])
    )
    
    # ---------------- 3. Heavy Rainfall & Waterlogging Risk ----------------
    rain_7d = weather.total_precipitation_7d_mm
    flood_score = 0.0
    if rain_7d > 120.0:
        flood_score = 90.0
        f_level = "Critical"
        f_impact = f"Torrential downpour ({rain_7d:.1f}mm in 7 days). High hazard of waterlogging, root asphyxiation, and topsoil erosion."
    elif rain_7d > 70.0:
        flood_score = 60.0
        f_level = "High"
        f_impact = f"Heavy localized rainfall ({rain_7d:.1f}mm). Watch field drainage channels and avoid fertilizer leaching."
    elif rain_7d > 35.0:
        flood_score = 30.0
        f_level = "Moderate"
        f_impact = "Moderate rains expected. Beneficial for rainfed soil recharge, minimal waterlogging hazard."
    else:
        flood_score = 10.0
        f_level = "Low"
        f_impact = f"Light or zero precipitation ({rain_7d:.1f}mm). No waterlogging or runoff risk."
        
    flood_metric = RiskMetric(
        category="Heavy Rainfall & Flood Risk",
        score_pct=flood_score,
        risk_level=f_level,
        primary_driver=f"Forecasted 7-day cumulative rainfall of {rain_7d:.1f}mm",
        impact_explanation=f_impact,
        alert_triggered=(f_level in ["High", "Critical"])
    )
    
    return drought_metric, heatwave_metric, flood_metric
