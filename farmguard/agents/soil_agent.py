"""
Soil Moisture & Agronomic Water Balance Agent.
Computes rootzone water depletion, crop water stress index (CWSI), and irrigation deficits.
"""
from typing import Dict, Any
from farmguard.models import FarmProfile, AgroWeatherData, RiskMetric
from farmguard.tools.soil_moisture_tool import analyze_soil_moisture_stress

class SoilAgronomyAgent:
    """Specialist agent focused on soil physics, rootzone moisture, and water balance."""
    
    def __init__(self, name: str = "SoilAgronomySpecialist"):
        self.name = name
        self.role = "Soil Physics & Rootzone Hydrologist"
        
    def evaluate(self, profile: FarmProfile, weather: AgroWeatherData) -> Dict[str, Any]:
        # Use average upper rootzone soil moisture (0-28cm) from weather telemetry
        effective_sm = (weather.avg_soil_moisture_0_7cm + weather.avg_soil_moisture_7_28cm) / 2.0
        
        soil_analysis = analyze_soil_moisture_stress(
            crop_name=profile.crop_name,
            growth_stage=profile.growth_stage,
            soil_type=profile.soil_type,
            current_soil_moisture_pct=effective_sm
        )
        
        metric: RiskMetric = soil_analysis["metric"]
        
        reasoning_step = {
            "agent": self.name,
            "role": self.role,
            "analysis": (
                f"Computed FAO-56 dual water balance for {profile.crop_name} in {profile.soil_type}. "
                f"Effective soil moisture is {effective_sm:.1f}%. TAW: {soil_analysis['taw_mm']}mm, "
                f"RAW buffer: {soil_analysis['raw_mm']}mm, Rootzone depletion: {soil_analysis['depletion_mm']}mm. "
                f"Crop Water Stress Index (CWSI): {soil_analysis['cwsi']} (Transpiration reduction: {(1-soil_analysis['ks_transpiration_factor'])*100:.0f}%)."
            )
        }
        
        return {
            "soil_analysis": soil_analysis,
            "soil_metric": metric,
            "reasoning": reasoning_step
        }
