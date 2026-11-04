"""
Resilience & Adaptive Farming Advisory Agent.
Synthesizes scientific agronomy recommendations tailored for smallholders.
"""
from typing import Dict, Any, List
from farmguard.models import FarmProfile, AgroWeatherData, RiskMetric, IrrigationDayAdvice
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES
from farmguard.tools.alert_tool import generate_irrigation_schedule_7d

class AdvisoryAgent:
    """Specialist agent focused on low-cost climate adaptation strategies."""
    
    def __init__(self, name: str = "ResilienceAdviser"):
        self.name = name
        self.role = "Climate Adaptation & Extension Specialist"
        
    def formulate_recommendations(
        self,
        profile: FarmProfile,
        weather: AgroWeatherData,
        drought_metric: RiskMetric,
        heatwave_metric: RiskMetric,
        soil_metric: RiskMetric,
        flood_metric: RiskMetric,
        soil_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        crop_info = CROP_DATABASE.get(profile.crop_name, CROP_DATABASE["Maize (Corn)"])
        soil_info = SOIL_PROPERTIES.get(profile.soil_type, SOIL_PROPERTIES["Loam"])
        
        immediate_actions: List[str] = []
        resilience_tips: List[str] = list(crop_info["resilience_interventions"])
        
        # Immediate actions based on active risk drivers
        if heatwave_metric.risk_level in ["Critical", "High"]:
            immediate_actions.append(
                f"🔥 High Heat Alert: Daytime temperatures reach {weather.max_forecast_temp_c}°C. Apply irrigation strictly during late evening/night to reduce evaporative losses and prevent canopy scorch."
            )
            if "flower" in profile.growth_stage.lower() or "anthesis" in profile.growth_stage.lower():
                immediate_actions.append(
                    "🌸 Anthesis Protection: Water crop roots today to maintain transpiration cooling and protect pollen viability."
                )
                
        if soil_metric.risk_level in ["Critical", "High"]:
            needed = soil_analysis.get("irrigation_needed_mm", 20.0)
            if profile.irrigation_access != "Rainfed Only":
                immediate_actions.append(
                    f"💧 Immediate Soil Recharge: Soil moisture has dropped below safe buffer. Apply ~{needed:.0f} mm of supplemental water."
                )
            else:
                immediate_actions.append(
                    "🍂 Immediate Mulching: Spread 5-10 cm of crop residue or dry grass over rootzones to slash soil evaporation by up to 50%."
                )
                
        if flood_metric.risk_level in ["Critical", "High"]:
            immediate_actions.append(
                f"🌧️ Heavy Rain Warning ({weather.total_precipitation_7d_mm:.1f}mm expected): Clear drainage ditches and reinforce field bunds immediately to avoid root waterlogging."
            )
            
        if not immediate_actions:
            immediate_actions.append("✅ Soil moisture and weather remain in optimal ranges. Proceed with standard weeding and monitoring.")
            immediate_actions.append("🌿 Scout underleaves for early pest/vector emergence triggered by warm weather.")
            
        # Add soil management tip
        resilience_tips.append(soil_info["management_tip"])
        
        # Generate 7-day irrigation schedule
        depletion = soil_analysis.get("depletion_mm", 15.0)
        raw = soil_analysis.get("raw_mm", 30.0)
        schedule: List[IrrigationDayAdvice] = generate_irrigation_schedule_7d(
            profile=profile,
            weather=weather,
            soil_depletion_mm=depletion,
            raw_mm=raw
        )
        
        reasoning_step = {
            "agent": self.name,
            "role": self.role,
            "analysis": (
                f"Synthesized localized adaptation plan for {profile.farmer_name}'s {profile.crop_name}. "
                f"Addressed {drought_metric.risk_level} drought, {heatwave_metric.risk_level} heat, and "
                f"{soil_metric.risk_level} soil deficit. Formulated {len(immediate_actions)} immediate actions "
                f"and a 7-day adaptive irrigation schedule."
            )
        }
        
        return {
            "immediate_actions": immediate_actions,
            "irrigation_schedule": schedule,
            "resilience_recommendations": resilience_tips,
            "reasoning": reasoning_step
        }
