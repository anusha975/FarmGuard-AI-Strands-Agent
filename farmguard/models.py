"""
Pydantic schemas and data models for FarmGuard AI.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class FarmProfile(BaseModel):
    farmer_name: str = Field(default="Smallholder Farmer")
    location_name: str = Field(..., description="Village, District or Region name")
    latitude: float = Field(..., description="Decimal latitude (-90 to 90)")
    longitude: float = Field(..., description="Decimal longitude (-180 to 180)")
    crop_name: str = Field(..., description="Cultivated crop name")
    growth_stage: str = Field(default="Flowering/Anthesis")
    soil_type: str = Field(default="Loam")
    field_size_hectares: float = Field(default=1.5, ge=0.1, le=100.0)
    irrigation_access: str = Field(default="Rainfed Only")
    language: str = Field(default="en", description="'en' for English, 'te' for Telugu")

class DailyForecastRecord(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    precip_mm: float
    et0_mm: float
    sm_0_7cm: float
    sm_7_28cm: float

class AgroWeatherData(BaseModel):
    location: str
    latitude: float
    longitude: float
    is_simulated: bool = False
    data_source: str = "🟢 LIVE DATA (Open-Meteo Agro-Weather API)"
    current_temp_c: float
    max_forecast_temp_c: float
    min_forecast_temp_c: float
    total_precipitation_7d_mm: float
    total_et0_7d_mm: float
    net_water_balance_mm: float
    avg_soil_moisture_pct: float
    heatwave_days_count: int
    consecutive_dry_days: int
    daily_forecasts: List[DailyForecastRecord] = []

class SoilHydrologyData(BaseModel):
    crop_name: str
    soil_type: str
    effective_root_depth_m: float
    field_capacity_pct: float
    permanent_wilting_point_pct: float
    current_moisture_pct: float
    total_available_water_taw_mm: float
    readily_available_water_raw_mm: float
    rootzone_depletion_mm: float
    crop_water_stress_index_cwsi: float
    stress_level: str
    irrigation_needed_mm: float
    soil_management_tip: str
    data_source: str

class RiskAssessmentData(BaseModel):
    drought_score_pct: float
    drought_level: str
    heatwave_score_pct: float
    heatwave_level: str
    flood_score_pct: float
    flood_level: str
    composite_vulnerability_index: float
    primary_hazard: str

# Backward compatibility alias
RiskMetric = RiskAssessmentData

class FarmGuardDiagnosis(BaseModel):
    farm_profile: FarmProfile
    weather_data: AgroWeatherData
    soil_data: SoilHydrologyData
    risk_assessment: RiskAssessmentData
    is_simulated: bool
    data_source_badge: str
    overall_status: str
    immediate_actions: List[str]
    resilience_recommendations: List[str]
    sms_alert_message: str
    safety_disclaimer: str
    tool_execution_trace: List[Dict[str, Any]] = []
