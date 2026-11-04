"""
FarmGuard Multi-Agent Orchestrator.
Supervises and coordinates domain agents to deliver an end-to-end climate resilience diagnosis.
"""
from typing import Dict, Any, List
from farmguard.models import FarmProfile, FarmGuardDiagnosis, AgroWeatherData, RiskMetric
from farmguard.agents.climate_agent import ClimateRiskAgent
from farmguard.agents.soil_agent import SoilAgronomyAgent
from farmguard.agents.advisory_agent import AdvisoryAgent
from farmguard.agents.bedrock_agent import BedrockStrandsAgentBridge
from farmguard.tools.alert_tool import format_farmer_sms_alert

class FarmGuardOrchestrator:
    """Master supervisor for FarmGuard multi-agent climate resilience workflow."""
    
    def __init__(self):
        self.climate_agent = ClimateRiskAgent()
        self.soil_agent = SoilAgronomyAgent()
        self.advisory_agent = AdvisoryAgent()
        self.bedrock_bridge = BedrockStrandsAgentBridge()
        
    def run_diagnosis(
        self,
        profile: FarmProfile,
        weather: AgroWeatherData = None
    ) -> FarmGuardDiagnosis:
        reasoning_trace: List[Dict[str, str]] = []
        
        # 1. Orchestrator Initialization
        reasoning_trace.append({
            "agent": "Orchestrator",
            "role": "Multi-Agent System Supervisor",
            "analysis": (
                f"Initiating climate risk assessment for farmer '{profile.farmer_name}' at "
                f"'{profile.location_name}' ({profile.latitude:.2f}°N, {profile.longitude:.2f}°E). "
                f"Target Crop: {profile.crop_name} (Stage: {profile.growth_stage}, Soil: {profile.soil_type}, "
                f"Irrigation: {profile.irrigation_access}). Delegating to ClimateRiskSpecialist."
            )
        })
        
        # 2. Climate Risk Evaluation
        climate_res = self.climate_agent.evaluate(profile, weather=weather)
        weather_data: AgroWeatherData = climate_res["weather"]
        drought_metric: RiskMetric = climate_res["drought_metric"]
        heatwave_metric: RiskMetric = climate_res["heatwave_metric"]
        flood_metric: RiskMetric = climate_res["flood_metric"]
        reasoning_trace.append(climate_res["reasoning"])
        
        # 3. Soil Moisture & Agronomy Evaluation
        soil_res = self.soil_agent.evaluate(profile, weather=weather_data)
        soil_metric: RiskMetric = soil_res["soil_metric"]
        soil_analysis: Dict[str, Any] = soil_res["soil_analysis"]
        reasoning_trace.append(soil_res["reasoning"])
        
        # 4. Advisory & Adaptation Synthesis
        advisory_res = self.advisory_agent.formulate_recommendations(
            profile=profile,
            weather=weather_data,
            drought_metric=drought_metric,
            heatwave_metric=heatwave_metric,
            soil_metric=soil_metric,
            flood_metric=flood_metric,
            soil_analysis=soil_analysis
        )
        reasoning_trace.append(advisory_res["reasoning"])
        
        # 5. Composite Vulnerability Index Calculation
        # Weighted agro-climatic hazard index
        composite_score = (
            (drought_metric.score_pct * 0.35) +
            (soil_metric.score_pct * 0.30) +
            (heatwave_metric.score_pct * 0.25) +
            (flood_metric.score_pct * 0.10)
        )
        composite_score = round(min(100.0, max(0.0, composite_score)), 1)
        
        if composite_score >= 70.0:
            overall_status = "Emergency"
        elif composite_score >= 50.0:
            overall_status = "High Warning"
        elif composite_score >= 30.0:
            overall_status = "Advisory Active"
        else:
            overall_status = "Normal"
            
        # Top active hazard for SMS headline
        all_metrics = [drought_metric, soil_metric, heatwave_metric, flood_metric]
        top_hazard = max(all_metrics, key=lambda m: m.score_pct)
        
        # Format farmer SMS dispatch
        sms_text = format_farmer_sms_alert(
            farmer_name=profile.farmer_name,
            crop=profile.crop_name,
            overall_status=overall_status,
            top_risk=top_hazard,
            immediate_actions=advisory_res["immediate_actions"]
        )
        
        reasoning_trace.append({
            "agent": "Orchestrator",
            "role": "Diagnosis Finalizer",
            "analysis": (
                f"Multi-agent synthesis complete. Composite Vulnerability Index: {composite_score:.1f}/100 "
                f"(Status: {overall_status}). Primary hazard driver: {top_hazard.category} ({top_hazard.score_pct:.1f}%). "
                f"Actionable SMS dispatched."
            )
        })
        
        return FarmGuardDiagnosis(
            farm_profile=profile,
            weather_summary=weather_data,
            drought_risk=drought_metric,
            heatwave_risk=heatwave_metric,
            soil_moisture_stress=soil_metric,
            rainfall_flood_risk=flood_metric,
            composite_vulnerability_index=composite_score,
            overall_status=overall_status,
            immediate_actions_today=advisory_res["immediate_actions"],
            irrigation_schedule_7d=advisory_res["irrigation_schedule"],
            agronomic_resilience_recommendations=advisory_res["resilience_recommendations"],
            sms_alert_message=sms_text,
            agent_reasoning_trace=reasoning_trace
        )
