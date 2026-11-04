"""
Alert and dispatch formatting tool for FarmGuard AI.
Formats concise, actionable farmer SMS alerts and advisory cards.
"""
from typing import List, Dict, Any
from farmguard.models import FarmProfile, AgroWeatherData, RiskMetric, IrrigationDayAdvice

def generate_irrigation_schedule_7d(
    profile: FarmProfile,
    weather: AgroWeatherData,
    soil_depletion_mm: float,
    raw_mm: float
) -> List[IrrigationDayAdvice]:
    """
    Generate an intelligent, day-by-day 7-day irrigation schedule tailored to
    smallholder water access, daily forecast temperatures, and anticipated rainfall.
    """
    schedule: List[IrrigationDayAdvice] = []
    accumulated_deficit = soil_depletion_mm
    
    for i, day in enumerate(weather.daily_forecasts):
        import datetime
        try:
            day_dt = datetime.date.fromisoformat(day.date)
            day_name = day_dt.strftime("%A (%b %d)")
        except Exception:
            day_name = f"Day {i+1} ({day.date})"
            
        daily_et = day.et0_fao_evapotranspiration
        daily_rain = day.precipitation_sum
        
        # Balance equation for today
        accumulated_deficit += (daily_et - daily_rain)
        
        if daily_rain >= 12.0:
            rec = "Withhold Irrigation"
            vol = "0 mm (Rain covers requirement)"
            reason = f"Substantial rainfall ({daily_rain:.1f}mm) expected. Avoid over-watering and nutrient leaching."
            accumulated_deficit = max(0.0, accumulated_deficit - daily_rain)
        elif day.temp_max >= 37.0 and profile.irrigation_access != "Rainfed Only":
            rec = "Evening Cooling Irrigation"
            vol = "15-20 mm / 3 hrs drip"
            reason = f"Extreme heat ({day.temp_max}°C). Apply water in late evening to lower canopy temp and prevent flower drop."
            accumulated_deficit = max(0.0, accumulated_deficit - 15.0)
        elif accumulated_deficit > raw_mm and profile.irrigation_access != "Rainfed Only":
            rec = "Critical Irrigation Required"
            vol = f"{min(35.0, round(accumulated_deficit, 1))} mm"
            reason = f"Soil moisture depletion breached crop safety threshold ({raw_mm:.1f}mm). Refill rootzone."
            accumulated_deficit = max(0.0, accumulated_deficit - 25.0)
        elif profile.irrigation_access == "Rainfed Only":
            if accumulated_deficit > raw_mm:
                rec = "Moisture Conservation Alert"
                vol = "N/A (Rainfed)"
                reason = "No irrigation source available. Apply organic straw/residue mulch immediately to reduce evaporation."
            else:
                rec = "Monitor Soil Surface"
                vol = "N/A (Rainfed)"
                reason = "Moisture currently adequate. Practice weed removal to eliminate moisture competition."
        else:
            rec = "Withhold / Monitor"
            vol = "0 mm"
            reason = "Rootzone moisture buffer is within safe range."
            
        schedule.append(
            IrrigationDayAdvice(
                date=day.date,
                day_name=day_name,
                recommendation=rec,
                volume_liters_or_mm=vol,
                rationale=reason
            )
        )
        
    return schedule


def format_farmer_sms_alert(
    farmer_name: str,
    crop: str,
    overall_status: str,
    top_risk: RiskMetric,
    immediate_actions: List[str]
) -> str:
    """
    Format concise, low-bandwidth text alert suitable for 2G SMS or automated IVR audio broadcast.
    Zero complex academic jargon; clear and direct.
    """
    header = f"🌾 FarmGuard Alert for {farmer_name} | {crop}"
    status_tag = f"Status: {overall_status.upper()}"
    hazard = f"Hazard: {top_risk.category} ({top_risk.risk_level.upper()}) - {top_risk.primary_driver}."
    
    actions_text = "\n".join([f"• {act}" for act in immediate_actions[:3]])
    
    return f"{header}\n{status_tag}\n{hazard}\nImmediate Steps:\n{actions_text}\n- FarmGuard AI Multi-Agent Engine"
