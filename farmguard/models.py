"""
Pydantic schemas and data structures for FarmGuard AI.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class FarmProfile(BaseModel):
    farmer_name: str = Field(default="Smallholder Farmer")
    location_name: str = Field(..., description="Village, District or Region name")
    latitude: float = Field(..., description="Decimal latitude (-90 to 90)")
    longitude: float = Field(..., description="Decimal longitude (-180 to 180)")
    crop_name: str = Field(..., description="Cultivated crop name")
    growth_stage: str = Field(
        default="Vegetative",
        description="Growth stage: Seedling, Vegetative, Flowering/Anthesis, Grain Filling, Maturity"
    )
    soil_type: str = Field(
        default="Loam",
        description="Soil texture: Sandy Soil, Sandy Loam, Loam, Clay Loam, Clay / Black Cotton Soil, Silt Loam"
    )
    field_size_hectares: float = Field(default=1.5, ge=0.1, le=100.0)
    irrigation_access: str = Field(
        default="Rainfed Only",
        description="Irrigation mode: Rainfed Only, Borewell, Drip System, Canal/Furrow, Farm Pond"
    )

class DailyAgroForecast(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    precipitation_sum: float
    et0_fao_evapotranspiration: float
    soil_moisture_0_7cm: float
    soil_moisture_7_28cm: float

class AgroWeatherData(BaseModel):
    location: str
    latitude: float
    longitude: float
    elevation_m: float = 0.0
    current_temp_c: float
    max_forecast_temp_c: float
    min_forecast_temp_c: float
    total_precipitation_7d_mm: float
    total_et0_7d_mm: float
    avg_soil_moisture_0_7cm: float
    avg_soil_moisture_7_28cm: float
    consecutive_dry_days: int
    heatwave_days_count: int
    daily_forecasts: List[DailyAgroForecast] = []
    forecast_summary: str = ""

class RiskMetric(BaseModel):
    category: str
    score_pct: float = Field(ge=0.0, le=100.0)
    risk_level: str  # "Low", "Moderate", "High", "Critical"
    primary_driver: str
    impact_explanation: str
    alert_triggered: bool = False

class IrrigationDayAdvice(BaseModel):
    date: str
    day_name: str
    recommendation: str  # "Irrigate", "Withhold Irrigation", "Light Evening Splash"
    volume_liters_or_mm: str
    rationale: str

class FarmGuardDiagnosis(BaseModel):
    farm_profile: FarmProfile
    weather_summary: AgroWeatherData
    drought_risk: RiskMetric
    heatwave_risk: RiskMetric
    soil_moisture_stress: RiskMetric
    rainfall_flood_risk: RiskMetric
    composite_vulnerability_index: float  # 0 to 100
    overall_status: str  # "Normal", "Advisory Active", "High Warning", "Emergency"
    immediate_actions_today: List[str]
    irrigation_schedule_7d: List[IrrigationDayAdvice]
    agronomic_resilience_recommendations: List[str]
    sms_alert_message: str
    agent_reasoning_trace: List[Dict[str, str]] = []
