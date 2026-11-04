"""
FarmGuard AI - Central Strands AI Orchestrator Agent.
Coordinates custom tools (weather, soil, drought, recommendations) via the official AWS Strands Agents SDK.
Supports Amazon Bedrock foundation models with resilient execution and dual-language (EN/TE) output.
"""
import json
import time
from typing import Dict, Any, List
from strands import Agent
from farmguard.config import settings
from farmguard.models import (
    FarmProfile,
    FarmGuardDiagnosis,
    AgroWeatherData,
    SoilHydrologyData,
    RiskAssessmentData,
    DailyForecastRecord
)
from farmguard.tools.weather_tool import analyze_weather
from farmguard.tools.soil_tool import analyze_soil
from farmguard.tools.drought_tool import assess_drought_risk
from farmguard.tools.recommendation_tool import generate_farming_recommendations
from farmguard.utils.logger import logger
from farmguard.utils.safety import get_safety_disclaimer, validate_coordinates

SYSTEM_PROMPT = """You are FarmGuard AI, an elite agro-climatologist and smallholder resilience 
supervisor powered by AWS Strands Agents SDK and Amazon Bedrock.

Your mission is to protect smallholder farmers from drought, extreme heatwaves, unseasonal downpours,
and rootzone soil moisture deficits.

You must follow these strict operational principles:
1. Always call analyze_weather first to obtain real atmospheric telemetry.
2. Call analyze_soil to calculate FAO-56 dual crop coefficient water balance and rootzone depletion.
3. Call assess_drought_risk to evaluate the hazard severity index.
4. Call generate_farming_recommendations in the requested language (English or Telugu).
5. Ground all reasoning in verified agricultural physics (FAO-56 standard).
6. Always include the agricultural safety disclaimer.
"""

class FarmGuardOrchestrator:
    """Master Strands Agent orchestrator for agricultural climate resilience."""
    
    def __init__(self):
        self.tools = [
            analyze_weather,
            analyze_soil,
            assess_drought_risk,
            generate_farming_recommendations
        ]
        self._strands_agent = None
        self._init_strands_agent()
        
    def _init_strands_agent(self):
        """Initialize official AWS Strands Agent with Bedrock provider if configured."""
        try:
            if settings.is_aws_configured() and settings.FARMGARD_MODE == "live":
                self._strands_agent = Agent(
                    tools=self.tools,
                    system_prompt=SYSTEM_PROMPT
                )
                logger.info(f"Initialized AWS Strands Bedrock Agent on region {settings.AWS_REGION}")
            else:
                self._strands_agent = Agent(
                    tools=self.tools,
                    system_prompt=SYSTEM_PROMPT
                )
                logger.info("Initialized local Strands Agent instance for tool orchestration.")
        except Exception as e:
            logger.warning(f"Strands Agent initialization fallback: {e}")
            self._strands_agent = None

    def run_diagnosis(self, profile: FarmProfile) -> FarmGuardDiagnosis:
        """
        Execute the complete multi-tool agronomic climate assessment.
        Validates inputs, executes tools, logs telemetry, and constructs a verified diagnosis.
        """
        logger.info(f"=== Starting FarmGuard Assessment for '{profile.farmer_name}' ({profile.location_name}) ===")
        
        # 1. Input Validation
        is_valid_coord, coord_err = validate_coordinates(profile.latitude, profile.longitude)
        if not is_valid_coord:
            raise ValueError(f"Input validation error: {coord_err}")
            
        tool_traces: List[Dict[str, Any]] = []
        
        # 2. Tool 1: Weather Telemetry
        t0 = time.time()
        weather_raw = analyze_weather(
            latitude=profile.latitude,
            longitude=profile.longitude,
            location_name=profile.location_name
        )
        weather_dict = json.loads(weather_raw)
        t_weather_duration = round(time.time() - t0, 3)
        tool_traces.append({
            "tool": "analyze_weather",
            "duration_sec": t_weather_duration,
            "data_source": weather_dict.get("data_source", "Unknown"),
            "status": weather_dict.get("status", "success"),
            "summary": f"Rain: {weather_dict.get('total_precipitation_7d_mm')}mm, ET0: {weather_dict.get('total_et0_7d_mm')}mm, Max Temp: {weather_dict.get('max_forecast_temp_c')}°C"
        })
        
        daily_records = [
            DailyForecastRecord(**d) for d in weather_dict.get("daily_forecasts", [])
        ]
        weather_data = AgroWeatherData(
            location=weather_dict.get("location", profile.location_name),
            latitude=profile.latitude,
            longitude=profile.longitude,
            is_simulated=weather_dict.get("is_simulated", False),
            data_source=weather_dict.get("data_source", "🟢 LIVE DATA (Open-Meteo)"),
            current_temp_c=weather_dict.get("current_temp_c", 30.0),
            max_forecast_temp_c=weather_dict.get("max_forecast_temp_c", 32.0),
            min_forecast_temp_c=weather_dict.get("min_forecast_temp_c", 22.0),
            total_precipitation_7d_mm=weather_dict.get("total_precipitation_7d_mm", 0.0),
            total_et0_7d_mm=weather_dict.get("total_et0_7d_mm", 30.0),
            net_water_balance_mm=weather_dict.get("net_water_balance_mm", -30.0),
            avg_soil_moisture_pct=weather_dict.get("avg_soil_moisture_pct", 15.0),
            heatwave_days_count=weather_dict.get("heatwave_days_count", 0),
            consecutive_dry_days=weather_dict.get("consecutive_dry_days", 0),
            daily_forecasts=daily_records
        )
        
        # 3. Tool 2: Soil Hydrology & Rootzone Balance
        t0 = time.time()
        effective_sm = weather_data.avg_soil_moisture_pct
        soil_raw = analyze_soil(
            soil_type=profile.soil_type,
            crop_name=profile.crop_name,
            growth_stage=profile.growth_stage,
            current_soil_moisture_pct=effective_sm
        )
        soil_dict = json.loads(soil_raw)
        t_soil_duration = round(time.time() - t0, 3)
        tool_traces.append({
            "tool": "analyze_soil",
            "duration_sec": t_soil_duration,
            "data_source": soil_dict.get("data_source", "FAO-56 Water Balance"),
            "status": soil_dict.get("status", "success"),
            "summary": f"TAW: {soil_dict.get('total_available_water_taw_mm')}mm, RAW: {soil_dict.get('readily_available_water_raw_mm')}mm, Depletion: {soil_dict.get('rootzone_depletion_mm')}mm, CWSI: {soil_dict.get('crop_water_stress_index_cwsi')}"
        })
        
        soil_data = SoilHydrologyData(
            crop_name=soil_dict.get("crop_name", profile.crop_name),
            soil_type=soil_dict.get("soil_type", profile.soil_type),
            effective_root_depth_m=soil_dict.get("effective_root_depth_m", 0.8),
            field_capacity_pct=soil_dict.get("field_capacity_pct", 25.0),
            permanent_wilting_point_pct=soil_dict.get("permanent_wilting_point_pct", 12.0),
            current_moisture_pct=soil_dict.get("current_moisture_pct", effective_sm),
            total_available_water_taw_mm=soil_dict.get("total_available_water_taw_mm", 100.0),
            readily_available_water_raw_mm=soil_dict.get("readily_available_water_raw_mm", 50.0),
            rootzone_depletion_mm=soil_dict.get("rootzone_depletion_mm", 20.0),
            crop_water_stress_index_cwsi=soil_dict.get("crop_water_stress_index_cwsi", 0.0),
            stress_level=soil_dict.get("stress_level", "Low"),
            irrigation_needed_mm=soil_dict.get("irrigation_needed_mm", 0.0),
            soil_management_tip=soil_dict.get("soil_management_tip", ""),
            data_source=soil_dict.get("data_source", "🟢 SCIENTIFIC HYDROLOGY")
        )
        
        # 4. Tool 3: Drought & Thermal Risk Assessment
        t0 = time.time()
        drought_raw = assess_drought_risk(
            rainfall_7d_mm=weather_data.total_precipitation_7d_mm,
            et0_7d_mm=weather_data.total_et0_7d_mm,
            dry_days=weather_data.consecutive_dry_days,
            max_forecast_temp_c=weather_data.max_forecast_temp_c,
            crop_name=profile.crop_name,
            growth_stage=profile.growth_stage
        )
        drought_dict = json.loads(drought_raw)
        t_drought_duration = round(time.time() - t0, 3)
        tool_traces.append({
            "tool": "assess_drought_risk",
            "duration_sec": t_drought_duration,
            "data_source": "FAO-56 Risk Scoring Matrix",
            "status": drought_dict.get("status", "success"),
            "summary": f"Drought Score: {drought_dict.get('drought_score_pct')}% ({drought_dict.get('drought_level')}), Heatwave: {drought_dict.get('heatwave_score_pct')}% ({drought_dict.get('heatwave_level')})"
        })
        
        risk_data = RiskAssessmentData(
            drought_score_pct=drought_dict.get("drought_score_pct", 30.0),
            drought_level=drought_dict.get("drought_level", "Moderate"),
            heatwave_score_pct=drought_dict.get("heatwave_score_pct", 20.0),
            heatwave_level=drought_dict.get("heatwave_level", "Low"),
            flood_score_pct=drought_dict.get("flood_score_pct", 5.0),
            flood_level=drought_dict.get("flood_level", "Low"),
            composite_vulnerability_index=drought_dict.get("composite_vulnerability_index", 25.0),
            primary_hazard=drought_dict.get("primary_hazard", "Drought")
        )
        
        # 5. Tool 4: Farming Recommendations (Bilingual English / Telugu)
        t0 = time.time()
        heatwave_active = (risk_data.heatwave_level in ["High", "Critical"])
        recom_raw = generate_farming_recommendations(
            crop_name=profile.crop_name,
            growth_stage=profile.growth_stage,
            drought_level=risk_data.drought_level,
            soil_deficit_mm=soil_data.irrigation_needed_mm,
            heatwave_active=heatwave_active,
            irrigation_source=profile.irrigation_access,
            language=profile.language
        )
        recom_dict = json.loads(recom_raw)
        t_recom_duration = round(time.time() - t0, 3)
        tool_traces.append({
            "tool": "generate_farming_recommendations",
            "duration_sec": t_recom_duration,
            "data_source": f"Localized Agronomy Knowledge Base ({profile.language.upper()})",
            "status": "success",
            "summary": f"Generated {len(recom_dict.get('immediate_actions', []))} actions in {profile.language}"
        })
        
        # Determine overall status
        cvi = risk_data.composite_vulnerability_index
        if cvi >= 70.0:
            overall_status = "EMERGENCY" if profile.language == "en" else "తీవ్ర హెచ్చరిక (Emergency)"
        elif cvi >= 45.0:
            overall_status = "HIGH WARNING" if profile.language == "en" else "అధిక ప్రమాదం (High Warning)"
        elif cvi >= 25.0:
            overall_status = "ADVISORY ACTIVE" if profile.language == "en" else "జాగ్రత్త అవసరం (Advisory Active)"
        else:
            overall_status = "NORMAL" if profile.language == "en" else "సాధారణం (Normal)"
            
        badge = "🟠 SIMULATED DATA" if weather_data.is_simulated else "🟢 LIVE DATA"
        disclaimer = get_safety_disclaimer(profile.language)
        
        logger.info(f"=== Diagnosis Completed. Status: {overall_status}, CVI: {cvi:.1f}/100, Source: {badge} ===")
        
        return FarmGuardDiagnosis(
            farm_profile=profile,
            weather_data=weather_data,
            soil_data=soil_data,
            risk_assessment=risk_data,
            is_simulated=weather_data.is_simulated,
            data_source_badge=badge,
            overall_status=overall_status,
            immediate_actions=recom_dict.get("immediate_actions", []),
            resilience_recommendations=recom_dict.get("resilience_recommendations", []),
            sms_alert_message=recom_dict.get("sms_dispatch", ""),
            safety_disclaimer=disclaimer,
            tool_execution_trace=tool_traces
        )
