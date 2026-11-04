"""
Automated unit tests for root agent.py and tools/ modules.
"""
import unittest
import json
from agent import get_farmguard_agent, run_farmguard_pipeline, FARMGUARD_TOOLS
from tools.weather import get_weather_forecast
from tools.soil import analyze_soil_moisture
from tools.drought import calculate_drought_risk
from tools.farming_advice import get_farming_recommendations

class TestStrandsBackend(unittest.TestCase):

    def test_agent_initialization(self):
        agent = get_farmguard_agent()
        self.assertIsNotNone(agent)
        self.assertEqual(len(agent.tool_names), 4)
        self.assertIn("get_weather_forecast", agent.tool_names)
        self.assertIn("analyze_soil_moisture", agent.tool_names)
        self.assertIn("calculate_drought_risk", agent.tool_names)
        self.assertIn("get_farming_recommendations", agent.tool_names)

    def test_weather_live_and_demo(self):
        # Demo mode
        demo_raw = get_weather_forecast(15.0, 78.0, "Demo Site", demo_mode=True)
        demo_data = json.loads(demo_raw)
        self.assertEqual(demo_data["status"], "success")
        self.assertTrue(demo_data["is_simulated"])
        self.assertIn("SIMULATED", demo_data["data_source"])

        # Invalid coord error handling
        err_raw = get_weather_forecast(95.0, 78.0, "Invalid Site")
        err_data = json.loads(err_raw)
        self.assertEqual(err_data["status"], "error")

    def test_soil_analysis_fao56(self):
        soil_raw = analyze_soil_moisture("Loam", "Maize (Corn)", "Vegetative", 25.0)
        data = json.loads(soil_raw)
        self.assertEqual(data["status"], "success")
        self.assertIn("total_available_water_taw_mm", data)
        self.assertIn("readily_available_water_raw_mm", data)
        self.assertEqual(data["soil_risk_level"], "Low")

    def test_drought_calculation(self):
        drought_raw = calculate_drought_risk(5.0, 35.0, 5, 38.0, "Sorghum", "Vegetative")
        data = json.loads(drought_raw)
        self.assertEqual(data["status"], "success")
        self.assertIn("drought_risk_level", data)
        self.assertIn("drought_drivers", data)

    def test_farming_advice_telugu(self):
        recom_raw = get_farming_recommendations("Groundnut (Peanut)", "Flowering", "High", 20.0, True, "Rainfed Only", "te")
        data = json.loads(recom_raw)
        self.assertEqual(data["status"], "success")
        self.assertIn("ఫామ్‌గార్డ్ అలర్ట్", data["sms_dispatch"])
        self.assertIn("బాధ్యతాయుతమైన ఏఐ", data["safety_disclaimer"])

    def test_pipeline_execution(self):
        profile = {
            "latitude": 17.38,
            "longitude": 78.48,
            "location_name": "Hyderabad Outskirts",
            "crop_name": "Tomato",
            "growth_stage": "Flowering/Anthesis",
            "soil_type": "Loam",
            "language": "en",
            "demo_mode": True
        }
        res = run_farmguard_pipeline(profile)
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["tool_traces"]), 4)

if __name__ == "__main__":
    unittest.main()
