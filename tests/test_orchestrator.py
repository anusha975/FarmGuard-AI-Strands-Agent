"""
Automated unit tests for FarmGuard Strands Orchestrator agent.
"""
import unittest
from farmguard.models import FarmProfile
from farmguard.orchestrator import FarmGuardOrchestrator
from farmguard.utils.safety import SAFETY_DISCLAIMER_EN, SAFETY_DISCLAIMER_TE

class TestFarmGuardOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orchestrator = FarmGuardOrchestrator()

    def test_orchestrator_full_workflow_english(self):
        profile = FarmProfile(
            farmer_name="Amina Mwangi",
            location_name="Dodoma, Tanzania",
            latitude=-6.16,
            longitude=35.74,
            crop_name="Sorghum",
            growth_stage="Flowering/Anthesis",
            soil_type="Sandy Loam",
            field_size_hectares=1.5,
            irrigation_access="Rainfed Only",
            language="en"
        )
        diag = self.orchestrator.run_diagnosis(profile)
        self.assertIsNotNone(diag)
        self.assertEqual(len(diag.tool_execution_trace), 4)
        
        # Verify all 4 tools were executed in the trace
        tool_names = [t["tool"] for t in diag.tool_execution_trace]
        self.assertEqual(
            tool_names,
            ["analyze_weather", "analyze_soil", "assess_drought_risk", "generate_farming_recommendations"]
        )
        self.assertIn("RESPONSIBLE AI", diag.safety_disclaimer)
        self.assertTrue(len(diag.immediate_actions) > 0)
        self.assertIn("FarmGuard Alert", diag.sms_alert_message)

    def test_orchestrator_full_workflow_telugu(self):
        profile = FarmProfile(
            farmer_name="రమేష్ నాయుడు",
            location_name="అనంతపురం, ఆంధ్రప్రదేశ్",
            latitude=14.68,
            longitude=77.60,
            crop_name="Groundnut (Peanut)",
            growth_stage="Flowering/Anthesis",
            soil_type="Sandy Loam",
            field_size_hectares=2.5,
            irrigation_access="Rainfed Only",
            language="te"
        )
        diag = self.orchestrator.run_diagnosis(profile)
        self.assertIsNotNone(diag)
        self.assertIn("బాధ్యతాయుతమైన ఏఐ", diag.safety_disclaimer)
        self.assertIn("ఫామ్‌గార్డ్ అలర్ట్", diag.sms_alert_message)

    def test_invalid_coordinates_validation(self):
        profile = FarmProfile(
            farmer_name="Test Farmer",
            location_name="Invalid Point",
            latitude=145.0,  # Invalid latitude > 90
            longitude=77.0,
            crop_name="Maize (Corn)"
        )
        with self.assertRaises(ValueError):
            self.orchestrator.run_diagnosis(profile)

if __name__ == "__main__":
    unittest.main()
