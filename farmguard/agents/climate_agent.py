"""
Climate & Weather Risk Specialist Agent.
Analyzes temperature extremes, dry spell duration, precipitation deficits, and atmospheric vapor pressure deficits.
"""
from typing import Dict, Any
from farmguard.models import FarmProfile, AgroWeatherData, RiskMetric
from farmguard.tools.weather_tool import fetch_agro_weather_telemetry
from farmguard.tools.drought_tool import calculate_climate_risks
from farmguard.data.crop_knowledge import CROP_DATABASE

class ClimateRiskAgent:
    """Specialist agent focused on agro-meteorological extremes."""
    
    def __init__(self, name: str = "ClimateRiskSpecialist"):
        self.name = name
        self.role = "Agro-Meteorological Extreme Event Analyst"
        
    def evaluate(self, profile: FarmProfile, weather: AgroWeatherData = None) -> Dict[str, Any]:
        crop_info = CROP_DATABASE.get(profile.crop_name, CROP_DATABASE["Maize (Corn)"])
        crit_temp = crop_info["critical_temp_max_c"]
        
        # Fetch or use passed weather telemetry
        if weather is None:
            weather = fetch_agro_weather_telemetry(
                latitude=profile.latitude,
                longitude=profile.longitude,
                location_name=profile.location_name,
                crop_critical_temp=crit_temp
            )
            
        drought_metric, heatwave_metric, flood_metric = calculate_climate_risks(
            weather=weather,
            crop_name=profile.crop_name,
            growth_stage=profile.growth_stage
        )
        
        reasoning_step = {
            "agent": self.name,
            "role": self.role,
            "analysis": (
                f"Evaluated 7-day atmospheric trajectory for {profile.location_name}. "
                f"Peak Temp: {weather.max_forecast_temp_c}°C (Threshold: {crit_temp}°C). "
                f"Cumulative Rain: {weather.total_precipitation_7d_mm:.1f}mm vs ET0: {weather.total_et0_7d_mm:.1f}mm. "
                f"Identified {drought_metric.risk_level} drought risk and {heatwave_metric.risk_level} heatwave stress."
            )
        }
        
        return {
            "weather": weather,
            "drought_metric": drought_metric,
            "heatwave_metric": heatwave_metric,
            "flood_metric": flood_metric,
            "reasoning": reasoning_step
        }
