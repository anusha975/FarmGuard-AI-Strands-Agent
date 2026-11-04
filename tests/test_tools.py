"""
Unit tests for FarmGuard AI scientific tools and calculation modules.
"""
import unittest
from farmguard.models import FarmProfile, AgroWeatherData, DailyAgroForecast
from farmguard.tools.soil_moisture_tool import analyze_soil_moisture_stress
from farmguard.tools.drought_tool import calculate_climate_risks
from farmguard.tools.alert_tool import generate_irrigation_schedule_7d, format_farmer_sms_alert

class TestFarmGuardTools(unittest.TestCase):
    
    def test_soil_moisture_stress_optimal(self):
        # In Loam: Field Capacity is ~27%, PWP is ~12%.
        # If moisture is 26%, it is well within RAW (no stress)
        res = analyze_soil_moisture_stress(
            crop_name="Maize (Corn)",
            growth_stage="Vegetative",
            soil_type="Loam",
            current_soil_moisture_pct=26.0
        )
        self.assertEqual(res["metric"].risk_level, "Low")
        self.assertEqual(res["cwsi"], 0.0)
        self.assertEqual(res["irrigation_needed_mm"], 0.0)
        
    def test_soil_moisture_stress_critical(self):
        # If moisture is below PWP (10%), critical stress
        res = analyze_soil_moisture_stress(
            crop_name="Maize (Corn)",
            growth_stage="Vegetative",
            soil_type="Loam",
            current_soil_moisture_pct=10.0
        )
        self.assertEqual(res["metric"].risk_level, "Critical")
        self.assertTrue(res["metric"].alert_triggered)
        self.assertGreater(res["depletion_mm"], res["raw_mm"])
        
    def test_drought_and_heatwave_detection(self):
        # Create hot, dry weather scenario
        forecasts = [
            DailyAgroForecast(
                date=f"2026-06-0{i+1}",
                temp_max=39.0,
                temp_min=26.0,
                precipitation_sum=0.0,
                et0_fao_evapotranspiration=6.5,
                soil_moisture_0_7cm=10.0,
                soil_moisture_7_28cm=14.0
            ) for i in range(7)
        ]
        
        weather = AgroWeatherData(
            location="Dryland Test Site",
            latitude=15.0,
            longitude=75.0,
            current_temp_c=38.5,
            max_forecast_temp_c=39.0,
            min_forecast_temp_c=26.0,
            total_precipitation_7d_mm=0.0,
            total_et0_7d_mm=45.5,
            avg_soil_moisture_0_7cm=10.0,
            avg_soil_moisture_7_28cm=14.0,
            consecutive_dry_days=7,
            heatwave_days_count=7,
            daily_forecasts=forecasts
        )
        
        drought, heatwave, flood = calculate_climate_risks(
            weather=weather,
            crop_name="Maize (Corn)",
            growth_stage="Flowering/Anthesis"
        )
        
        self.assertIn(drought.risk_level, ["High", "Critical"])
        self.assertIn(heatwave.risk_level, ["High", "Critical"])
        self.assertEqual(flood.risk_level, "Low")
        self.assertTrue(drought.alert_triggered)
        self.assertTrue(heatwave.alert_triggered)

    def test_rain_withholding_in_schedule(self):
        profile = FarmProfile(
            farmer_name="Amina",
            location_name="Dodoma",
            latitude=-6.16,
            longitude=35.74,
            crop_name="Sorghum",
            growth_stage="Vegetative",
            soil_type="Sandy Loam",
            irrigation_access="Borewell / Tube-well"
        )
        
        # Heavy rain day
        forecasts = [
            DailyAgroForecast(
                date="2026-03-10",
                temp_max=28.0,
                temp_min=20.0,
                precipitation_sum=25.0,  # 25mm rain
                et0_fao_evapotranspiration=3.0,
                soil_moisture_0_7cm=25.0,
                soil_moisture_7_28cm=25.0
            )
        ]
        
        weather = AgroWeatherData(
            location="Dodoma",
            latitude=-6.16,
            longitude=35.74,
            current_temp_c=25.0,
            max_forecast_temp_c=28.0,
            min_forecast_temp_c=20.0,
            total_precipitation_7d_mm=25.0,
            total_et0_7d_mm=3.0,
            avg_soil_moisture_0_7cm=25.0,
            avg_soil_moisture_7_28cm=25.0,
            consecutive_dry_days=0,
            heatwave_days_count=0,
            daily_forecasts=forecasts
        )
        
        schedule = generate_irrigation_schedule_7d(profile, weather, soil_depletion_mm=10.0, raw_mm=20.0)
        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0].recommendation, "Withhold Irrigation")

if __name__ == "__main__":
    unittest.main()
