"""
Unit and Integration Tests for AWS Bedrock Configuration & Safe Error Handling.
Verifies credentials detection, IAM permission templates, and failure degradation paths.
"""
import unittest
from unittest.mock import patch, MagicMock
import botocore.exceptions
from farmguard.aws_bedrock import (
    check_aws_credentials_safe,
    check_bedrock_access,
    get_iam_policy_template,
    SUPPORTED_BEDROCK_MODELS,
    get_aws_region,
    get_bedrock_model_id
)
from agent import synthesize_bedrock_advisory, get_farmguard_agent


class TestAWSBedrockIntegration(unittest.TestCase):
    
    def test_safe_credentials_detection_does_not_reveal_secrets(self):
        """Verify credential check inspects environment safely without leaking secrets."""
        status = check_aws_credentials_safe()
        self.assertIn("configured", status)
        self.assertIn("auth_method", status)
        self.assertIn("env_vars_set", status)
        self.assertIn("region", status)
        
        # Verify no secret values are contained in the output keys
        for key, val in status["env_vars_set"].items():
            self.assertIsInstance(val, bool, f"Key {key} should only be a boolean flag, not a value.")

    def test_bedrock_access_graceful_handling_without_credentials(self):
        """When AWS credentials are not configured, test that check_bedrock_access returns clean error."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("farmguard.aws_bedrock.check_aws_credentials_safe") as mock_safe:
                mock_safe.return_value = {
                    "configured": False,
                    "auth_method": "none",
                    "env_vars_set": {},
                    "has_credentials_file": False,
                    "has_config_file": False,
                    "region": "us-east-1"
                }
                res = check_bedrock_access()
                self.assertFalse(res["configured"])
                self.assertFalse(res["model_accessible"])
                self.assertEqual(res["error_type"], "NoCredentialsError")
                self.assertIn(".env", res["remediation"])

    def test_iam_policy_least_privilege(self):
        """Verify IAM policy includes least-privilege Bedrock actions and no wildcard admin."""
        policy = get_iam_policy_template()
        self.assertEqual(policy["Version"], "2012-10-17")
        statements = policy["Statement"]
        
        # Find model access statement
        invocation_stmt = next(s for s in statements if s["Sid"] == "FarmGuardBedrockModelAccess")
        self.assertEqual(invocation_stmt["Effect"], "Allow")
        self.assertIn("bedrock:InvokeModel", invocation_stmt["Action"])
        self.assertIn("bedrock:InvokeModelWithResponseStream", invocation_stmt["Action"])
        
        # Ensure it targets foundation models, not wildcard admin
        for res in invocation_stmt["Resource"]:
            self.assertTrue(res.startswith("arn:aws:bedrock:*::foundation-model/"))

    def test_synthesize_bedrock_advisory_degrades_gracefully_on_no_credentials(self):
        """Synthesizing Bedrock advisory without credentials must not raise an exception."""
        profile = {
            "crop_name": "Groundnut (Peanut)",
            "growth_stage": "Flowering/Anthesis",
            "location_name": "Anantapur"
        }
        weather = {"total_precipitation_7d_mm": 5.0}
        soil = {"crop_water_stress_index_cwsi": 0.35, "irrigation_needed_mm": 12.0}
        drought = {"composite_vulnerability_index": 28.0, "drought_risk_level": "Moderate"}
        
        with patch("agent.check_aws_credentials_safe") as mock_safe:
            mock_safe.return_value = {"configured": False}
            res = synthesize_bedrock_advisory(profile, weather, soil, drought, language="en")
            self.assertFalse(res["bedrock_active"])
            self.assertEqual(res["error_type"], "NoCredentialsError")
            self.assertIn("Agronomic Science", res["message"])

    def test_synthesize_bedrock_advisory_handles_client_access_denied(self):
        """Handle AccessDeniedException gracefully when model access has not been granted."""
        profile = {"crop_name": "Maize", "growth_stage": "Vegetative", "location_name": "Warangal"}
        weather = {"total_precipitation_7d_mm": 0.0}
        soil = {"crop_water_stress_index_cwsi": 0.70, "irrigation_needed_mm": 25.0}
        drought = {"composite_vulnerability_index": 65.0, "drought_risk_level": "High"}

        with patch("agent.check_aws_credentials_safe") as mock_safe:
            mock_safe.return_value = {"configured": True}
            with patch("agent.BedrockModel"):
                with patch("agent.Agent") as mock_agent_cls:
                    mock_agent = MagicMock()
                    mock_agent.side_effect = botocore.exceptions.ClientError(
                        {"Error": {"Code": "AccessDeniedException", "Message": "Model access is restricted"}},
                        "InvokeModel"
                    )
                    mock_agent_cls.return_value = mock_agent

                    res = synthesize_bedrock_advisory(profile, weather, soil, drought, language="en")
                    self.assertFalse(res["bedrock_active"])
                    self.assertEqual(res["error_type"], "AccessDeniedException")
                    self.assertIn("Model Access", res["remediation"])

    def test_supported_models_dictionary(self):
        """Verify Claude 3.5 Sonnet and Nova models are in supported catalogue with pricing."""
        self.assertIn("anthropic.claude-3-5-sonnet-20240620-v1:0", SUPPORTED_BEDROCK_MODELS)
        self.assertIn("anthropic.claude-3-haiku-20240307-v1:0", SUPPORTED_BEDROCK_MODELS)
        self.assertIn("amazon.nova-lite-v1:0", SUPPORTED_BEDROCK_MODELS)
        self.assertIn("amazon.nova-pro-v1:0", SUPPORTED_BEDROCK_MODELS)
        for mid, meta in SUPPORTED_BEDROCK_MODELS.items():
            self.assertGreater(meta["pricing_input_per_1k"], 0)
            self.assertGreater(meta["pricing_output_per_1k"], 0)


if __name__ == "__main__":
    unittest.main()
