"""
Tools package exports for FarmGuard AI.
"""
from tools.weather import get_weather_forecast
from tools.soil import analyze_soil_moisture
from tools.drought import calculate_drought_risk
from tools.farming_advice import get_farming_recommendations

__all__ = [
    "get_weather_forecast",
    "analyze_soil_moisture",
    "calculate_drought_risk",
    "get_farming_recommendations",
]

