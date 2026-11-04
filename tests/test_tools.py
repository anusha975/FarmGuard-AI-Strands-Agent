"""
Automated unit tests for FarmGuard custom Strands tools.
"""
import unittest
import json
from farmguard.tools.weather_tool import analyze_weather
from farmguard.tools.soil_tool import analyze_soil
from farmguard.tools.drought_tool import assess_drought_risk
from farmguard.tools.recommendation_tool import generate_farming_recommendations

class TestFarmGuardStrandsTools(unittest.TestCase):

    def test_weather_tool_execution(self):
        # Rayalaseema Groundnut site: 14.68°N, 77.60°E (Anantapur)
        raw_res = analyze_weather(latitude=14.68, longitude=77.60, location_name="Anantapur")
        data = json.loads(raw_res)
        self.assertEqual(data["status"], "success")
        self.assertIn("data_source", data)
        self.assertIn("max_forecast_temp_c", data)
        self.assertIn("total_precipitation_7d_mm", data)
        self.assertIn("daily_forecasts", data)
        self.assertEqual(len(data["daily_forecasts"]), 7)

    def test_soil_tool_fao56_physics(self):
        # In Loam, FC is 27%, PWP is 12%. At 10% moisture, it's below PWP
        raw_res = analyze_soil(
            soil_type="Loam",
            crop_name="Maize (Corn)",
            growth_stage="Vegetative",
            current_soil_moisture_pct=10.0
        )
        data = json.loads(raw_res)
        self.assertEqual(data["status"], "CRITICAL_WILTING_POINT_BREACHED")
        self.assertGreater(data["crop_water_stress_index_cwsi"], 0.5)
        self.assertGreater(data["irrigation_needed_mm"], 0.0)

    def test_drought_risk_scoring(self):
        raw_res = assess_drought_risk(
            rainfall_7d_mm=0.0,
            et0_7d_mm=42.0,
            dry_days=7,
            max_forecast_temp_c=39.5,
            crop_name="Chickpea (Gram)",
            growth_stage="Flowering/Anthesis"
        )
        data = json.loads(raw_res)
        self.assertEqual(data["status"], "success")
        self.assertIn(data["drought_level"], ["High", "Critical"])
        self.assertIn(data["heatwave_level"], ["High", "Critical"])
        self.assertGreaterEqual(data["composite_vulnerability_index"], 50.0)

    def test_recommendation_tool_bilingual(self):
        # English
        raw_en = generate_farming_recommendations(
            crop_name="Groundnut (Peanut)",
            growth_stage="Flowering/Anthesis",
            drought_level="Critical",
            soil_deficit_mm=25.0,
            heatwave_active=True,
            irrigation_source="Rainfed Only",
            language="en"
        )
        data_en = json.loads(raw_en)
        self.assertGreater(len(data_en["immediate_actions"]), 0)
        self.assertIn("FarmGuard Alert", data_en["sms_dispatch"])

        # Telugu
        raw_te = generate_farming_recommendations(
            crop_name="Groundnut (Peanut)",
            growth_stage="Flowering/Anthesis",
            drought_level="Critical",
            soil_deficit_mm=25.0,
            heatwave_active=True,
            irrigation_source="Rainfed Only",
            language="te"
        )
        data_te = json.loads(raw_te)
        self.assertGreater(len(data_te["immediate_actions"]), 0)
        self.assertIn("ఫామ్‌గార్డ్ అలర్ట్", data_te["sms_dispatch"])

if __name__ == "__main__":
    unittest.main()
