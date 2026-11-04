"""
Weather Analysis Tool for FarmGuard AI.
Decorated with @tool for direct execution by the AWS Strands Agent.
Queries Open-Meteo Agro-Weather API or provides explicit deterministic simulation.
"""
import json
import datetime
from typing import Dict, Any
import requests
from strands import tool
from farmguard.config import settings
from farmguard.utils.logger import logger

@tool
def analyze_weather(latitude: float, longitude: float, location_name: str = "Farm Site") -> str:
    """
    Fetch and analyze real-time agro-meteorological telemetry for a farm.
    
    Args:
        latitude: Decimal latitude of the farm location (-90.0 to 90.0)
        longitude: Decimal longitude of the farm location (-180.0 to 180.0)
        location_name: Optional name of the farm or village
        
    Returns:
        JSON string containing 7-day weather metrics, ET0 evaporative demand,
        precipitation sums, dry days, heatwave metrics, and data source flag.
    """
    logger.info(f"[Tool: analyze_weather] Ingesting coordinates ({latitude}, {longitude}) for {location_name}")
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "et0_fao_evapotranspiration",
            "soil_moisture_0_to_7cm_mean",
            "soil_moisture_7_to_28cm_mean"
        ],
        "current": ["temperature_2m", "relative_humidity_2m", "precipitation"],
        "timezone": "auto",
        "forecast_days": 7
    }
    
    try:
        response = requests.get(settings.OPEN_METEO_BASE_URL, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        daily = data.get("daily", {})
        
        time_list = daily.get("time", [])
        temp_max_list = daily.get("temperature_2m_max", [])
        temp_min_list = daily.get("temperature_2m_min", [])
        precip_list = daily.get("precipitation_sum", [])
        et0_list = daily.get("et0_fao_evapotranspiration", [])
        sm_07_list = daily.get("soil_moisture_0_to_7cm_mean", [])
        sm_728_list = daily.get("soil_moisture_7_to_28cm_mean", [])
        
        daily_records = []
        heatwave_days = 0
        consecutive_dry = 0
        current_streak = 0
        
        for i in range(len(time_list)):
            t_max = temp_max_list[i] if i < len(temp_max_list) and temp_max_list[i] is not None else 32.0
            t_min = temp_min_list[i] if i < len(temp_min_list) and temp_min_list[i] is not None else 22.0
            precip = precip_list[i] if i < len(precip_list) and precip_list[i] is not None else 0.0
            et0 = et0_list[i] if i < len(et0_list) and et0_list[i] is not None else 4.5
            sm_07 = (sm_07_list[i] * 100.0) if i < len(sm_07_list) and sm_07_list[i] is not None else 15.0
            sm_728 = (sm_728_list[i] * 100.0) if i < len(sm_728_list) and sm_728_list[i] is not None else 20.0
            
            if t_max >= 36.0:
                heatwave_days += 1
            if precip < 1.0:
                current_streak += 1
                consecutive_dry = max(consecutive_dry, current_streak)
            else:
                current_streak = 0
                
            daily_records.append({
                "date": time_list[i],
                "temp_max": round(t_max, 1),
                "temp_min": round(t_min, 1),
                "precip_mm": round(precip, 1),
                "et0_mm": round(et0, 2),
                "sm_0_7cm": round(sm_07, 1),
                "sm_7_28cm": round(sm_728, 1)
            })
            
        total_precip = sum(d["precip_mm"] for d in daily_records)
        total_et0 = sum(d["et0_mm"] for d in daily_records)
        avg_sm_07 = sum(d["sm_0_7cm"] for d in daily_records) / max(1, len(daily_records))
        avg_sm_728 = sum(d["sm_7_28cm"] for d in daily_records) / max(1, len(daily_records))
        
        result = {
            "status": "success",
            "is_simulated": False,
            "data_source": "🟢 LIVE DATA (Open-Meteo Agro-Weather API)",
            "location": location_name,
            "coordinates": {"lat": latitude, "lon": longitude},
            "current_temp_c": round(data.get("current", {}).get("temperature_2m", temp_max_list[0] if temp_max_list else 30.0), 1),
            "max_forecast_temp_c": round(max(temp_max_list) if temp_max_list else 30.0, 1),
            "min_forecast_temp_c": round(min(temp_min_list) if temp_min_list else 20.0, 1),
            "total_precipitation_7d_mm": round(total_precip, 1),
            "total_et0_7d_mm": round(total_et0, 1),
            "net_water_balance_mm": round(total_precip - total_et0, 1),
            "avg_soil_moisture_pct": round((avg_sm_07 + avg_sm_728) / 2.0, 1),
            "heatwave_days_count": heatwave_days,
            "consecutive_dry_days": consecutive_dry,
            "daily_forecasts": daily_records
        }
        return json.dumps(result)
        
    except Exception as exc:
        logger.warning(f"[Tool: analyze_weather] Live API unavailable ({exc}). Using deterministic simulation.")
        today = datetime.date.today()
        sim_records = []
        temps_max = [35.0, 37.5, 38.5, 37.0, 34.5, 33.0, 32.5]
        temps_min = [23.0, 25.0, 26.0, 25.5, 24.0, 22.5, 21.5]
        precips = [0.0, 0.0, 0.0, 0.0, 1.5, 0.0, 0.0]
        et0s = [5.5, 6.2, 6.8, 6.4, 5.2, 4.8, 4.5]
        
        for i in range(7):
            d_date = (today + datetime.timedelta(days=i)).isoformat()
            sim_records.append({
                "date": d_date,
                "temp_max": temps_max[i],
                "temp_min": temps_min[i],
                "precip_mm": precips[i],
                "et0_mm": et0s[i],
                "sm_0_7cm": 12.5,
                "sm_7_28cm": 16.0
            })
            
        result = {
            "status": "success",
            "is_simulated": True,
            "data_source": "🟠 SIMULATED DATA (FAO-56 Semi-Arid Dryland Model)",
            "location": location_name,
            "coordinates": {"lat": latitude, "lon": longitude},
            "current_temp_c": 35.0,
            "max_forecast_temp_c": 38.5,
            "min_forecast_temp_c": 21.5,
            "total_precipitation_7d_mm": 1.5,
            "total_et0_7d_mm": 39.4,
            "net_water_balance_mm": -37.9,
            "avg_soil_moisture_pct": 14.2,
            "heatwave_days_count": 4,
            "consecutive_dry_days": 4,
            "daily_forecasts": sim_records
        }
        return json.dumps(result)
