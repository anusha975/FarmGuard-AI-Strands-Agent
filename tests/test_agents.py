"""
Integration tests for FarmGuard multi-agent pipeline and orchestrator.
"""
import unittest
from farmguard.models import FarmProfile
from farmguard.agents.orchestrator import FarmGuardOrchestrator

class TestMultiAgentOrchestrator(unittest.TestCase):
    
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
            irrigation_access="Rainfed Only"
        )
        
        diagnosis = self.orchestrator.run_diagnosis(profile)
        
        self.assertIsNotNone(diagnosis)
        self.assertEqual(diagnosis.farm_profile.farmer_name, "Ramesh Kumar")
        self.assertGreaterEqual(diagnosis.composite_vulnerability_index, 0.0)
        self.assertLessEqual(diagnosis.composite_vulnerability_index, 100.0)
        
        # Verify multi-agent reasoning trace presence
        self.assertGreaterEqual(len(diagnosis.agent_reasoning_trace), 4)
        agent_names = [step["agent"] for step in diagnosis.agent_reasoning_trace]
        self.assertIn("Orchestrator", agent_names)
        self.assertIn("ClimateRiskSpecialist", agent_names)
        self.assertIn("SoilAgronomySpecialist", agent_names)
        self.assertIn("ResilienceAdviser", agent_names)
        
        # Verify 7-day irrigation schedule generated
        self.assertEqual(len(diagnosis.irrigation_schedule_7d), 7)
        
        # Verify immediate actions
        self.assertGreater(len(diagnosis.immediate_actions_today), 0)
        
        # Verify SMS text is populated
        self.assertTrue(len(diagnosis.sms_alert_message) > 20)
        self.assertIn("Ramesh Kumar", diagnosis.sms_alert_message)

if __name__ == "__main__":
    unittest.main()
