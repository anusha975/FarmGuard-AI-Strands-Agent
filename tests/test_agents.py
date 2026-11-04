"""
Integration tests for FarmGuard Strands Orchestrator agent.
"""
import unittest
from farmguard.models import FarmProfile
from farmguard.orchestrator import FarmGuardOrchestrator

class TestFarmGuardAgentWorkflow(unittest.TestCase):
    
    def setUp(self):
        self.orchestrator = FarmGuardOrchestrator()
        
    def test_end_to_end_orchestration(self):
        profile = FarmProfile(
            farmer_name="Ramesh Kumar",
            location_name="Vidarbha, Maharashtra",
            latitude=20.93,
            longitude=77.75,
            crop_name="Chickpea (Gram)",
            growth_stage="Flowering/Anthesis",
            soil_type="Clay / Black Cotton Soil (Vertisol)",
            field_size_hectares=2.0,
            irrigation_access="Rainfed Only",
            language="en"
        )
        
        diagnosis = self.orchestrator.run_diagnosis(profile)
        
        self.assertIsNotNone(diagnosis)
        self.assertEqual(diagnosis.farm_profile.farmer_name, "Ramesh Kumar")
        self.assertGreaterEqual(diagnosis.risk_assessment.composite_vulnerability_index, 0.0)
        self.assertLessEqual(diagnosis.risk_assessment.composite_vulnerability_index, 100.0)
        
        # Verify tool execution trace presence
        self.assertEqual(len(diagnosis.tool_execution_trace), 4)
        tool_names = [t["tool"] for t in diagnosis.tool_execution_trace]
        self.assertIn("analyze_weather", tool_names)
        self.assertIn("analyze_soil", tool_names)
        self.assertIn("assess_drought_risk", tool_names)
        self.assertIn("generate_farming_recommendations", tool_names)
        
        # Verify immediate actions
        self.assertGreater(len(diagnosis.immediate_actions), 0)
        
        # Verify SMS text is populated
        self.assertTrue(len(diagnosis.sms_alert_message) > 20)
        self.assertIn("FarmGuard Alert", diagnosis.sms_alert_message)

if __name__ == "__main__":
    unittest.main()
