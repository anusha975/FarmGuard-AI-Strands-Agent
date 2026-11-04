"""
FarmGuard AI - Comprehensive Senior QA Automated Test Suite.
Validates the entire end-to-end system across all 13 critical requirements:
1. Strands Agent Initialization
2. Custom Tool Execution
3. Weather Input Validation
4. Soil Moisture Calculations (FAO-56 Dual Crop Physics)
5. Drought Classification
6. Farming Recommendations
7. English Responses
8. Telugu Responses
9. Invalid Inputs Handling
10. Missing Data Resilience
11. API Failure & Network Fault Tolerance
12. AWS Bedrock Integration & Fallback
13. Streamlit Interface & Visual Component Rendering
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import plotly.graph_objects as go
import botocore.exceptions
import requests

from agent import get_farmguard_agent, run_farmguard_pipeline, synthesize_bedrock_advisory, FARMGUARD_TOOLS
from tools.weather import get_weather_forecast
from tools.soil import analyze_soil_moisture
from tools.drought import calculate_drought_risk
from tools.farming_advice import get_farming_recommendations
from farmguard.aws_bedrock import (
    check_aws_credentials_safe,
    check_bedrock_access,
    get_iam_policy_template,
    SUPPORTED_BEDROCK_MODELS
)
from ui.components import render_vulnerability_gauge, render_weather_charts


class Test01StrandsAgentInitialization(unittest.TestCase):
    """Requirement 1: Strands Agent Initialization."""

    def test_agent_creates_with_bedrock_provider_and_tools(self):
        agent = get_farmguard_agent()
        self.assertIsNotNone(agent)
        # Check all 4 custom tools are registered in agent.tool_names
        registered = agent.tool_names
        self.assertEqual(len(registered), 4)
        self.assertIn("get_weather_forecast", registered)
        self.assertIn("analyze_soil_moisture", registered)
        self.assertIn("calculate_drought_risk", registered)
        self.assertIn("get_farming_recommendations", registered)

    def test_agent_system_prompt_integrity(self):
        agent = get_farmguard_agent()
        self.assertIsNotNone(agent.system_prompt)
        self.assertIn("FarmGuard AI", agent.system_prompt)
        self.assertIn("FAO-56", agent.system_prompt)
        self.assertIn("Telugu", agent.system_prompt)


class Test02CustomToolExecution(unittest.TestCase):
    """Requirement 2: Custom Tool Execution."""

    def test_weather_tool_executes_demo(self):
        raw = get_weather_forecast(14.68, 77.60, "Anantapur", demo_mode=True)
        data = json.loads(raw)
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["is_simulated"])
        self.assertIn("max_forecast_temp_c", data)
        self.assertIn("daily_forecasts", data)
        self.assertEqual(len(data["daily_forecasts"]), 7)

    def test_soil_tool_executes_valid(self):
        raw = analyze_soil_moisture("Loam", "Maize (Corn)", "Flowering/Anthesis", 22.0)
        data = json.loads(raw)
        self.assertEqual(data["status"], "success")
        self.assertIn("total_available_water_taw_mm", data)
        self.assertIn("crop_water_stress_index_cwsi", data)
        self.assertIn("soil_management_tip", data)

    def test_drought_tool_executes_valid(self):
        raw = calculate_drought_risk(5.0, 35.0, 4, 37.0, "Groundnut (Peanut)", "Flowering/Anthesis")
        data = json.loads(raw)
        self.assertEqual(data["status"], "success")
        self.assertIn("composite_vulnerability_index", data)
        self.assertIn("drought_risk_level", data)
        self.assertIn("drought_drivers", data)

    def test_farming_advice_tool_executes_valid(self):
        raw = get_farming_recommendations("Groundnut (Peanut)", "Flowering/Anthesis", "Moderate", 15.0, False, "Borewell", "en")
        data = json.loads(raw)
        self.assertEqual(data["status"], "success")
        self.assertIn("immediate_actions", data)
        self.assertIn("sms_dispatch", data)
        self.assertIn("safety_disclaimer", data)


class Test03WeatherInputValidation(unittest.TestCase):
    """Requirement 3: Weather Input Validation."""

    def test_latitude_above_upper_bound(self):
        raw = get_weather_forecast(95.0, 78.0, "North Pole Exceeded")
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")
        self.assertIn("latitude", data["message"].lower())

    def test_latitude_below_lower_bound(self):
        raw = get_weather_forecast(-91.5, 78.0, "South Pole Exceeded")
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")

    def test_longitude_out_of_bounds(self):
        raw = get_weather_forecast(15.0, 195.0, "Invalid Longitude")
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")
        self.assertIn("longitude", data["message"].lower())

    def test_non_numeric_coordinates(self):
        # Type error check
        raw = get_weather_forecast("invalid_lat", 78.0)  # type: ignore
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")


class Test04SoilMoistureCalculations(unittest.TestCase):
    """Requirement 4: Soil Moisture Calculations (FAO-56 Dual Crop Water Balance)."""

    def test_fao56_mathematical_consistency(self):
        # Loam: FC = 27%, PWP = 12% -> difference = 15% (0.15)
        # Maize Vegetative/Mid-stage Zr = 1.0m
        # Expected TAW = 1000 * 0.15 * 1.0 = 150.0 mm
        raw = analyze_soil_moisture("Loam", "Maize (Corn)", "Vegetative", 20.0)
        data = json.loads(raw)
        self.assertEqual(data["total_available_water_taw_mm"], 150.0)
        # RAW = p * TAW. For maize p = 0.55 -> RAW = 0.55 * 150.0 = 82.5 mm
        self.assertEqual(data["readily_available_water_raw_mm"], 82.5)

    def test_soil_moisture_below_wilting_point(self):
        # Loam PWP is 12%. At 8.0%, moisture is breached
        raw = analyze_soil_moisture("Loam", "Maize (Corn)", "Vegetative", 8.0)
        data = json.loads(raw)
        self.assertEqual(data["crop_water_stress_index_cwsi"], 1.0)
        self.assertEqual(data["soil_risk_level"], "Critical")
        self.assertIn("CRITICAL", data["agronomic_reason"])

    def test_soil_moisture_at_field_capacity(self):
        # Loam FC is 27%. At 28.0%, no water stress
        raw = analyze_soil_moisture("Loam", "Maize (Corn)", "Vegetative", 28.0)
        data = json.loads(raw)
        self.assertEqual(data["crop_water_stress_index_cwsi"], 0.0)
        self.assertEqual(data["irrigation_needed_mm"], 0.0)
        self.assertEqual(data["soil_risk_level"], "Low")

    def test_unknown_crop_and_soil_graceful_fallback(self):
        # Unrecognized crop/soil strings should default safely
        raw = analyze_soil_moisture("Martian Red Regolith", "Extraterrestrial Bean", "Vegetative", 20.0)
        data = json.loads(raw)
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["total_available_water_taw_mm"], 0.0)


class Test05DroughtClassification(unittest.TestCase):
    """Requirement 5: Drought Classification."""

    def test_extreme_drought_classification(self):
        # 0 rain, 45mm ET0, 7 dry days -> Critical drought
        raw = calculate_drought_risk(0.0, 45.0, 7, 39.0, "Groundnut (Peanut)", "Flowering/Anthesis")
        data = json.loads(raw)
        self.assertIn(data["drought_risk_level"], ["High", "Critical"])
        self.assertGreaterEqual(data["composite_vulnerability_index"], 60.0)
        self.assertTrue(len(data["drought_drivers"]) >= 2)

    def test_flood_risk_classification(self):
        # 90mm rainfall in 7 days -> Flood hazard
        raw = calculate_drought_risk(90.0, 20.0, 0, 28.0, "Rice (Lowland / Paddy)", "Vegetative")
        data = json.loads(raw)
        self.assertIn(data["flood_risk_level"], ["Moderate", "High", "Critical"])
        self.assertEqual(data["drought_risk_level"], "Low")

    def test_heatwave_risk_classification(self):
        # 42°C is above critical threshold for Maize (38°C)
        raw = calculate_drought_risk(10.0, 30.0, 3, 42.0, "Maize (Corn)", "Flowering/Anthesis")
        data = json.loads(raw)
        self.assertIn(data["heatwave_risk_level"], ["High", "Critical"])

    def test_cvi_composite_index_weighting(self):
        raw = calculate_drought_risk(15.0, 30.0, 3, 32.0, "Sorghum", "Vegetative")
        data = json.loads(raw)
        cvi = data["composite_vulnerability_index"]
        self.assertGreaterEqual(cvi, 0.0)
        self.assertLessEqual(cvi, 100.0)


class Test06FarmingRecommendations(unittest.TestCase):
    """Requirement 6: Farming Recommendations."""

    def test_immediate_tactical_actions_generated(self):
        raw = get_farming_recommendations("Chickpea (Gram)", "Flowering/Anthesis", "High", 25.0, True, "Rainfed Only", "en")
        data = json.loads(raw)
        actions = data["immediate_actions"]
        self.assertGreater(len(actions), 0)
        # Should contain heatwave cooling or mulching directive
        action_text = " ".join(actions).lower()
        self.assertTrue("mulch" in action_text or "evaporat" in action_text or "water" in action_text)

    def test_irrigation_mode_differentiation(self):
        # Rainfed advice should emphasize water conservation / mulching
        raw_rainfed = get_farming_recommendations("Maize (Corn)", "Flowering/Anthesis", "High", 25.0, False, "Rainfed Only", "en")
        data_rainfed = json.loads(raw_rainfed)
        
        # Drip advice should provide volumetric scheduling
        raw_drip = get_farming_recommendations("Maize (Corn)", "Flowering/Anthesis", "High", 25.0, False, "Drip System", "en")
        data_drip = json.loads(raw_drip)

        self.assertNotEqual(data_rainfed["immediate_actions"], data_drip["immediate_actions"])


class Test07EnglishResponses(unittest.TestCase):
    """Requirement 7: English Responses."""

    def test_english_language_output(self):
        raw = get_farming_recommendations("Groundnut (Peanut)", "Flowering/Anthesis", "Critical", 30.0, True, "Rainfed Only", "en")
        data = json.loads(raw)
        self.assertEqual(data["language"], "en")
        self.assertIn("FarmGuard Alert", data["sms_dispatch"])
        self.assertIn("RESPONSIBLE AI & AGRICULTURAL SAFETY", data["safety_disclaimer"])
        self.assertTrue(all(isinstance(a, str) and len(a) > 5 for a in data["immediate_actions"]))


class Test08TeluguResponses(unittest.TestCase):
    """Requirement 8: Telugu Responses (తెలుగు స్థానికీకరణ)."""

    def test_telugu_language_output_and_unicode(self):
        raw = get_farming_recommendations("Groundnut (Peanut)", "Flowering/Anthesis", "Critical", 30.0, True, "Rainfed Only", "te")
        data = json.loads(raw)
        self.assertEqual(data["language"], "te")
        # Assert Telugu characters exist in SMS and disclaimer
        self.assertIn("ఫామ్‌గార్డ్ అలర్ట్", data["sms_dispatch"])
        self.assertIn("బాధ్యతాయుతమైన ఏఐ", data["safety_disclaimer"])
        self.assertIn("హెచ్చరిక", data["sms_dispatch"])
        # Immediate actions must contain Telugu Unicode range \u0C00-\u0C7F
        has_telugu = any(any('\u0c00' <= char <= '\u0c7f' for char in action) for action in data["immediate_actions"])
        self.assertTrue(has_telugu, "Immediate actions must contain Telugu characters when language='te'")


class Test09InvalidInputsHandling(unittest.TestCase):
    """Requirement 9: Invalid Inputs."""

    def test_pipeline_raises_on_invalid_latitude(self):
        profile = {"latitude": 95.0, "longitude": 77.0}
        with self.assertRaises(ValueError):
            run_farmguard_pipeline(profile)

    def test_pipeline_raises_on_invalid_longitude(self):
        profile = {"latitude": 15.0, "longitude": -195.0}
        with self.assertRaises(ValueError):
            run_farmguard_pipeline(profile)

    def test_soil_negative_moisture_error(self):
        raw = analyze_soil_moisture("Loam", "Maize (Corn)", "Vegetative", -5.0)
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")

    def test_soil_excessive_moisture_error(self):
        raw = analyze_soil_moisture("Loam", "Maize (Corn)", "Vegetative", 120.0)
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")

    def test_drought_negative_rainfall(self):
        raw = calculate_drought_risk(-10.0, 30.0, 3, 35.0, "Maize", "Vegetative")
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")

    def test_drought_negative_et0(self):
        raw = calculate_drought_risk(10.0, -5.0, 3, 35.0, "Maize", "Vegetative")
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")

    def test_drought_invalid_dry_days(self):
        raw = calculate_drought_risk(10.0, 30.0, 10, 35.0, "Maize", "Vegetative")  # dry_days > 7
        data = json.loads(raw)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "ValidationError")


class Test10MissingDataResilience(unittest.TestCase):
    """Requirement 10: Missing Data."""

    def test_pipeline_with_minimal_profile_keys(self):
        # Profile providing only required coordinates; optional keys missing
        profile = {
            "latitude": 14.68,
            "longitude": 77.60,
            "demo_mode": True
        }
        res = run_farmguard_pipeline(profile)
        self.assertEqual(res["status"], "success")
        self.assertIn("weather", res)
        self.assertIn("soil", res)
        self.assertIn("drought", res)
        self.assertIn("recommendations", res)

    def test_weather_daily_records_none_values_imputed(self):
        # Open-Meteo returns nulls on sensor gap
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "daily": {
                "time": ["2026-11-04", "2026-11-05"],
                "temperature_2m_max": [None, 34.0],
                "temperature_2m_min": [20.0, None],
                "precipitation_sum": [None, 0.0],
                "et0_fao_evapotranspiration": [None, 5.0],
                "soil_moisture_0_to_7cm_mean": [None, 0.15],
                "soil_moisture_7_to_28cm_mean": [None, 0.20]
            },
            "current": {"temperature_2m": 30.0}
        }
        with patch("requests.get", return_value=mock_response):
            raw = get_weather_forecast(15.0, 78.0, "Gap Farm")
            data = json.loads(raw)
            self.assertEqual(data["status"], "success")
            self.assertIsNotNone(data["max_forecast_temp_c"])
            self.assertIsNotNone(data["total_precipitation_7d_mm"])


class Test11APIFailuresAndFaultTolerance(unittest.TestCase):
    """Requirement 11: API Failures."""

    def test_open_meteo_http_500_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        
        with patch("requests.get", return_value=mock_response):
            raw = get_weather_forecast(14.68, 77.60, "Server Down Site")
            data = json.loads(raw)
            self.assertEqual(data["status"], "error")
            self.assertEqual(data["error_type"], "NetworkError")
            self.assertIn("Open-Meteo", data["message"])

    def test_open_meteo_network_timeout(self):
        with patch("requests.get", side_effect=requests.exceptions.Timeout("Connection timed out")):
            raw = get_weather_forecast(14.68, 77.60, "Timeout Site")
            data = json.loads(raw)
            self.assertEqual(data["status"], "error")
            self.assertEqual(data["error_type"], "NetworkError")

    def test_open_meteo_connection_error(self):
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError("DNS failure")):
            raw = get_weather_forecast(14.68, 77.60, "Offline Site")
            data = json.loads(raw)
            self.assertEqual(data["status"], "error")
            self.assertEqual(data["error_type"], "NetworkError")

    def test_pipeline_catches_weather_api_failure_cleanly(self):
        profile = {"latitude": 15.0, "longitude": 78.0, "demo_mode": False}
        with patch("tools.weather.requests.get", side_effect=requests.exceptions.ConnectionError("No route")):
            res = run_farmguard_pipeline(profile)
            self.assertEqual(res["status"], "error")
            self.assertEqual(res["error_type"], "NetworkError")
            self.assertEqual(res["tool_traces"][0]["status"], "failed")


class Test12AWSBedrockConnectionAndDegradation(unittest.TestCase):
    """Requirement 12: AWS Bedrock Connection & Safe Error Handling."""

    def test_aws_credentials_inspection_is_safe(self):
        res = check_aws_credentials_safe()
        self.assertIn("configured", res)
        self.assertIn("auth_method", res)
        # Ensure no secrets leak
        for k, v in res["env_vars_set"].items():
            self.assertIsInstance(v, bool)

    def test_bedrock_access_denied_exception_handling(self):
        profile = {"crop_name": "Groundnut", "growth_stage": "Flowering", "location_name": "Anantapur"}
        weather = {"total_precipitation_7d_mm": 5.0}
        soil = {"crop_water_stress_index_cwsi": 0.35, "irrigation_needed_mm": 12.0}
        drought = {"composite_vulnerability_index": 28.0, "drought_risk_level": "Moderate"}

        with patch("agent.check_aws_credentials_safe", return_value={"configured": True}):
            with patch("agent.BedrockModel"):
                with patch("agent.Agent") as mock_agent_cls:
                    mock_agent = MagicMock()
                    mock_agent.side_effect = botocore.exceptions.ClientError(
                        {"Error": {"Code": "AccessDeniedException", "Message": "Model invocation blocked"}},
                        "InvokeModel"
                    )
                    mock_agent_cls.return_value = mock_agent

                    res = synthesize_bedrock_advisory(profile, weather, soil, drought, language="en")
                    self.assertFalse(res["bedrock_active"])
                    self.assertEqual(res["error_type"], "AccessDeniedException")
                    self.assertIn("Model Access", res["remediation"])

    def test_bedrock_throttling_exception_handling(self):
        profile = {"crop_name": "Maize", "growth_stage": "Vegetative", "location_name": "Guntur"}
        weather = {"total_precipitation_7d_mm": 0.0}
        soil = {"crop_water_stress_index_cwsi": 0.50, "irrigation_needed_mm": 20.0}
        drought = {"composite_vulnerability_index": 45.0, "drought_risk_level": "High"}

        with patch("agent.check_aws_credentials_safe", return_value={"configured": True}):
            with patch("agent.BedrockModel"):
                with patch("agent.Agent") as mock_agent_cls:
                    mock_agent = MagicMock()
                    mock_agent.side_effect = botocore.exceptions.ClientError(
                        {"Error": {"Code": "ThrottlingException", "Message": "Rate limit exceeded"}},
                        "InvokeModel"
                    )
                    mock_agent_cls.return_value = mock_agent

                    res = synthesize_bedrock_advisory(profile, weather, soil, drought, language="en")
                    self.assertFalse(res["bedrock_active"])
                    self.assertEqual(res["error_type"], "ThrottlingException")

    def test_bedrock_successful_synthesis_mock(self):
        profile = {"crop_name": "Sorghum", "growth_stage": "Grain Filling", "location_name": "Mahabubnagar"}
        weather = {"total_precipitation_7d_mm": 10.0}
        soil = {"crop_water_stress_index_cwsi": 0.20, "irrigation_needed_mm": 8.0}
        drought = {"composite_vulnerability_index": 22.0, "drought_risk_level": "Low"}

        with patch("agent.check_aws_credentials_safe", return_value={"configured": True}):
            with patch("agent.BedrockModel"):
                with patch("agent.Agent") as mock_agent_cls:
                    mock_agent = MagicMock()
                    mock_agent.return_value = "Bedrock synthesized agronomic executive narrative."
                    mock_agent_cls.return_value = mock_agent

                    res = synthesize_bedrock_advisory(profile, weather, soil, drought, language="en")
                    self.assertTrue(res["bedrock_active"])
                    self.assertEqual(res["status"], "success")
                    self.assertIn("Bedrock synthesized", res["narrative"])


class Test13StreamlitInterfaceAndVisualComponents(unittest.TestCase):
    """Requirement 13: Streamlit Interface & Visual Component Rendering."""

    def test_gauge_cvi_figure_creation(self):
        fig_low = render_vulnerability_gauge(18.0, "NORMAL", "en")
        self.assertIsInstance(fig_low, go.Figure)

        fig_high = render_vulnerability_gauge(75.0, "EMERGENCY", "te")
        self.assertIsInstance(fig_high, go.Figure)

    def test_weather_charts_rendering_with_mock_ui(self):
        weather_payload = {
            "daily_forecasts": [
                {"date": "2026-11-04", "temp_max_c": 36.0, "temp_min_c": 22.0, "precip_mm": 0.0, "et0_mm": 5.0},
                {"date": "2026-11-05", "temp_max_c": 37.5, "temp_min_c": 23.0, "precip_mm": 0.0, "et0_mm": 5.5},
            ]
        }
        with patch("streamlit.columns") as mock_cols:
            col1 = MagicMock()
            col2 = MagicMock()
            mock_cols.return_value = (col1, col2)
            with patch("streamlit.plotly_chart") as mock_chart:
                render_weather_charts(weather_payload, crit_temp_c=35.0)
                self.assertEqual(mock_chart.call_count, 2)

    def test_ui_diagnosis_payload_completeness(self):
        profile = {
            "latitude": 14.68,
            "longitude": 77.60,
            "crop_name": "Groundnut (Peanut)",
            "soil_type": "Sandy Loam",
            "language": "en",
            "demo_mode": True
        }
        res = run_farmguard_pipeline(profile)
        # Verify required keys for Streamlit render_diagnosis_dashboard
        required_keys = ["status", "is_simulated", "data_source", "overall_status", "composite_vulnerability_index", "weather", "soil", "drought", "recommendations", "aws_bedrock_status", "tool_traces"]
        for k in required_keys:
            self.assertIn(k, res, f"Missing key '{k}' in diagnosis payload required for Streamlit rendering.")


if __name__ == "__main__":
    unittest.main()
