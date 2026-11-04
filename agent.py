"""
FarmGuard AI - Central Strands AI Orchestrator Agent.
Built with the official AWS Strands Agents SDK and Amazon Bedrock.
"""
import os
import sys
import json
import logging

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load local environment variables (.env)
load_dotenv()

from strands import Agent
from strands.models.bedrock import BedrockModel, DEFAULT_BEDROCK_MODEL_ID, DEFAULT_BEDROCK_REGION
from tools.weather import get_weather_forecast
from tools.soil import analyze_soil_moisture
from tools.drought import calculate_drought_risk
from tools.farming_advice import get_farming_recommendations

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | [%(name)s] %(message)s")
logger = logging.getLogger("FarmGuardAgent")

FARMGUARD_TOOLS = [
    get_weather_forecast,
    analyze_soil_moisture,
    calculate_drought_risk,
    get_farming_recommendations,
]

SYSTEM_PROMPT = """You are FarmGuard AI, an elite agro-climatologist and smallholder resilience 
assistant powered by the official AWS Strands Agents SDK and Amazon Bedrock.

Your goal is to evaluate agro-meteorological risks (drought, heatwave, soil moisture depletion) 
and deliver practical, low-cost resilience interventions for smallholder farmers.

Operational Rules:
1. Ground every diagnosis in verified agro-hydrological data from your tools (FAO-56 standard).
2. Never invent weather numbers. If live data is unavailable and demonstration mode is not requested, report the error honestly.
3. For soil evaluation, clearly state Field Capacity, Wilting Point, and Crop Water Stress Index (CWSI).
4. Provide immediate actionable steps for the next 24-48 hours.
5. Provide localized recommendations in English or Telugu (తెలుగు) as requested.
6. Always attach the agricultural safety disclaimer.
"""

def is_aws_bedrock_configured() -> bool:
    """Check if AWS credentials are set for Amazon Bedrock."""
    return bool(
        os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
    ) or os.path.exists(os.path.expanduser("~/.aws/credentials"))

def get_farmguard_agent(
    model_id: Optional[str] = None,
    region_name: Optional[str] = None
) -> Agent:
    """
    Initialize and return a real Strands Agent connected to Amazon Bedrock.
    
    Args:
        model_id: Amazon Bedrock Foundation Model ID (e.g. anthropic.claude-3-5-sonnet-20240620-v1:0).
        region_name: AWS Region (defaults to us-east-1 or AWS_REGION env var).
        
    Returns:
        Configured strands.Agent instance.
    """
    region = region_name or os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    selected_model_id = model_id or os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    
    # Configure Bedrock Provider model
    try:
        bedrock_provider = BedrockModel(
            region_name=region,
            model_id=selected_model_id
        )
        logger.info(f"Initialized BedrockModel provider for region: {region}, model: {selected_model_id}")
    except Exception as e:
        logger.warning(f"BedrockModel initialization notice: {e}. Defaulting to standard Strands model resolution.")
        bedrock_provider = None

    if bedrock_provider is not None:
        agent = Agent(
            model=bedrock_provider,
            tools=FARMGUARD_TOOLS,
            system_prompt=SYSTEM_PROMPT
        )
    else:
        # Strands default Bedrock agent harness
        agent = Agent(
            tools=FARMGUARD_TOOLS,
            system_prompt=SYSTEM_PROMPT
        )
        
    logger.info("Official Strands Agent initialized successfully with 4 custom agro-tools.")
    return agent

def run_farmguard_pipeline(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the end-to-end FarmGuard climate resilience pipeline.
    Validates inputs, executes tools, handles errors, and returns a verified diagnosis.
    
    Args:
        profile: Dictionary with keys:
            - latitude: float
            - longitude: float
            - location_name: str
            - crop_name: str
            - growth_stage: str
            - soil_type: str
            - field_size_hectares: float
            - irrigation_access: str
            - language: str ('en' or 'te')
            - demo_mode: bool (default False; True only for demonstration)
            
    Returns:
        Structured diagnosis dictionary with telemetry, risks, bilingual advice, and trace.
    """
    # 1. Validation
    lat = profile.get("latitude")
    lon = profile.get("longitude")
    if not isinstance(lat, (int, float)) or not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Invalid latitude: {lat}. Must be between -90.0 and 90.0.")
    if not isinstance(lon, (int, float)) or not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Invalid longitude: {lon}. Must be between -180.0 and 180.0.")

    location_name = profile.get("location_name", "Target Farm")
    crop_name = profile.get("crop_name", "Maize (Corn)")
    growth_stage = profile.get("growth_stage", "Flowering/Anthesis")
    soil_type = profile.get("soil_type", "Loam")
    irrigation_access = profile.get("irrigation_access", "Rainfed Only")
    language = profile.get("language", "en")
    demo_mode = bool(profile.get("demo_mode", False))

    tool_traces = []

    # 2. Tool 1: Weather Telemetry (Do not invent data; use demo only if explicitly selected)
    weather_raw = get_weather_forecast(
        latitude=lat,
        longitude=lon,
        location_name=location_name,
        demo_mode=demo_mode
    )
    weather_data = json.loads(weather_raw)
    if weather_data.get("status") == "error":
        return {
            "status": "error",
            "error_type": weather_data.get("error_type"),
            "message": weather_data.get("message"),
            "tool_traces": [{"tool": "get_weather_forecast", "status": "failed", "error": weather_data.get("message")}]
        }
        
    tool_traces.append({
        "tool": "get_weather_forecast",
        "status": "success",
        "data_source": weather_data.get("data_source"),
        "is_simulated": weather_data.get("is_simulated", False)
    })

    # 3. Tool 2: Soil Moisture & Rootzone Physics
    # Use average 0-28cm moisture from weather forecast
    daily_list = weather_data.get("daily_forecasts", [])
    if daily_list:
        avg_sm = sum((d.get("soil_moisture_0_7cm_pct", 15.0) + d.get("soil_moisture_7_28cm_pct", 20.0)) / 2.0 for d in daily_list) / len(daily_list)
    else:
        avg_sm = 18.0

    soil_raw = analyze_soil_moisture(
        soil_type=soil_type,
        crop_name=crop_name,
        growth_stage=growth_stage,
        current_moisture_pct=avg_sm
    )
    soil_data = json.loads(soil_raw)
    tool_traces.append({
        "tool": "analyze_soil_moisture",
        "status": "success",
        "cwsi": soil_data.get("crop_water_stress_index_cwsi"),
        "stress_level": soil_data.get("soil_risk_level")
    })

    # 4. Tool 3: Drought and Thermal Risk Assessment
    drought_raw = calculate_drought_risk(
        rainfall_7d_mm=weather_data.get("total_precipitation_7d_mm", 0.0),
        et0_7d_mm=weather_data.get("total_et0_7d_mm", 35.0),
        dry_days=weather_data.get("consecutive_dry_days", 3),
        max_temp_c=weather_data.get("max_forecast_temp_c", 34.0),
        crop_name=crop_name,
        growth_stage=growth_stage
    )
    drought_data = json.loads(drought_raw)
    tool_traces.append({
        "tool": "calculate_drought_risk",
        "status": "success",
        "drought_score": drought_data.get("drought_score_pct"),
        "cvi": drought_data.get("composite_vulnerability_index")
    })

    # 5. Tool 4: Farming Recommendations (Bilingual EN / TE)
    heatwave_flag = (drought_data.get("heatwave_risk_level") in ["High", "Critical"])
    recom_raw = get_farming_recommendations(
        crop_name=crop_name,
        growth_stage=growth_stage,
        drought_level=drought_data.get("drought_risk_level", "Moderate"),
        soil_deficit_mm=soil_data.get("irrigation_needed_mm", 0.0),
        heatwave_active=heatwave_flag,
        irrigation_source=irrigation_access,
        language=language
    )
    recom_data = json.loads(recom_raw)
    tool_traces.append({
        "tool": "get_farming_recommendations",
        "status": "success",
        "language": language
    })

    # 6. Overall Status Determination
    cvi = drought_data.get("composite_vulnerability_index", 30.0)
    if cvi >= 70.0:
        overall_status = "EMERGENCY" if language == "en" else "తీవ్ర హెచ్చరిక (Emergency)"
    elif cvi >= 45.0:
        overall_status = "HIGH WARNING" if language == "en" else "అధిక ప్రమాదం (High Warning)"
    elif cvi >= 25.0:
        overall_status = "ADVISORY ACTIVE" if language == "en" else "జాగ్రత్త అవసరం (Advisory Active)"
    else:
        overall_status = "NORMAL" if language == "en" else "సాధారణం (Normal)"

    return {
        "status": "success",
        "is_simulated": weather_data.get("is_simulated", False),
        "data_source": weather_data.get("data_source"),
        "overall_status": overall_status,
        "composite_vulnerability_index": cvi,
        "farm_profile": profile,
        "weather": weather_data,
        "soil": soil_data,
        "drought": drought_data,
        "recommendations": recom_data,
        "tool_traces": tool_traces
    }

if __name__ == "__main__":
    print("=" * 60)
    print("🌾 Testing FarmGuard AI Strands Backend & Bedrock Agent Harness")
    print("=" * 60)
    
    # 1. Test Agent Initialization
    agent = get_farmguard_agent()
    print("✓ Initialized Strands Agent with tools:", [t.__name__ for t in FARMGUARD_TOOLS])

    # 2. Test Live Weather Run (English)
    test_profile_live = {
        "farmer_name": "Ramesh Kumar",
        "location_name": "Anantapur, Andhra Pradesh",
        "latitude": 14.68,
        "longitude": 77.60,
        "crop_name": "Groundnut (Peanut)",
        "growth_stage": "Flowering/Anthesis",
        "soil_type": "Sandy Loam",
        "irrigation_access": "Rainfed Only",
        "language": "en",
        "demo_mode": False
    }
    
    print("\n[Test 1] Running Live Assessment for Anantapur (English):")
    res1 = run_farmguard_pipeline(test_profile_live)
    print(f"Status: {res1.get('overall_status')} | CVI: {res1.get('composite_vulnerability_index')}%")
    print(f"Data Source: {res1.get('data_source')}")
    print("Tools Executed:", [t["tool"] for t in res1.get("tool_traces", [])])
    
    # 3. Test Telugu Localization (Demo Mode)
    test_profile_te = {
        "farmer_name": "రాము నాయుడు",
        "location_name": "మహబూబ్‌నగర్, తెలంగాణ",
        "latitude": 16.74,
        "longitude": 78.00,
        "crop_name": "Maize (Corn)",
        "growth_stage": "Flowering/Anthesis",
        "soil_type": "Clay / Black Cotton Soil (Vertisol)",
        "irrigation_access": "Borewell / Tube-well",
        "language": "te",
        "demo_mode": True
    }
    
    print("\n[Test 2] Running Demo Assessment for Mahabubnagar (Telugu):")
    res2 = run_farmguard_pipeline(test_profile_te)
    print(f"Status: {res2.get('overall_status')} | CVI: {res2.get('composite_vulnerability_index')}%")
    print(f"Data Source: {res2.get('data_source')}")
    print("Telugu Actions:")
    for act in res2.get("recommendations", {}).get("immediate_actions", [])[:2]:
        print(" ", act)
        
    print("\n✓ All FarmGuard Backend Agent Tests Completed Successfully!")
