"""
FarmGuard AI - Amazon Bedrock & AWS Integration Manager.
Handles AWS credentials detection, IAM permission validation, Bedrock model access checks,
and safe error handling for the Strands Agents SDK.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import boto3
import botocore.exceptions
from dotenv import load_dotenv

# Load local environment variables from .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger("FarmGuardAWS")

# Recommended Bedrock Foundation Models for Smallholder Agricultural Resilience
SUPPORTED_BEDROCK_MODELS = {
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
        "provider": "Anthropic",
        "name": "Claude 3.5 Sonnet v1",
        "pricing_input_per_1k": 0.003,
        "pricing_output_per_1k": 0.015,
        "recommended_for": "Complex multi-hazard synthesis and reasoning"
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "provider": "Anthropic",
        "name": "Claude 3 Haiku",
        "pricing_input_per_1k": 0.00025,
        "pricing_output_per_1k": 0.00125,
        "recommended_for": "Ultra-low-latency 2G SMS and IVR voice dispatch"
    },
    "amazon.nova-lite-v1:0": {
        "provider": "Amazon",
        "name": "Amazon Nova Lite",
        "pricing_input_per_1k": 0.00006,
        "pricing_output_per_1k": 0.00024,
        "recommended_for": "Cost-optimized multilingual translation and alerts"
    },
    "amazon.nova-pro-v1:0": {
        "provider": "Amazon",
        "name": "Amazon Nova Pro",
        "pricing_input_per_1k": 0.0008,
        "pricing_output_per_1k": 0.0032,
        "recommended_for": "High-accuracy agronomic planning"
    }
}

DEFAULT_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
DEFAULT_REGION = "us-east-1"


def get_aws_region() -> str:
    """Retrieve AWS region from environment or default to us-east-1."""
    return (
        os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or DEFAULT_REGION
    )


def get_bedrock_model_id() -> str:
    """Retrieve Bedrock model ID from environment or default to Claude 3.5 Sonnet."""
    return os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)


def check_aws_credentials_safe() -> Dict[str, Any]:
    """
    Safely inspect AWS credentials availability WITHOUT ever exposing secret values.
    Returns status metadata.
    """
    env_keys = {
        "AWS_ACCESS_KEY_ID": bool(os.getenv("AWS_ACCESS_KEY_ID")),
        "AWS_SECRET_ACCESS_KEY": bool(os.getenv("AWS_SECRET_ACCESS_KEY")),
        "AWS_SESSION_TOKEN": bool(os.getenv("AWS_SESSION_TOKEN")),
        "AWS_PROFILE": bool(os.getenv("AWS_PROFILE")),
    }
    
    home_aws = Path.home() / ".aws"
    cred_file_exists = (home_aws / "credentials").exists()
    config_file_exists = (home_aws / "config").exists()
    
    # Check boto3 credential resolution without printing keys
    boto_has_creds = False
    auth_method = "none"
    try:
        session = boto3.Session()
        creds = session.get_credentials()
        if creds:
            boto_has_creds = True
            auth_method = creds.method
    except Exception as e:
        logger.debug(f"Error checking boto3 credentials: {e}")

    return {
        "configured": boto_has_creds,
        "auth_method": auth_method,
        "env_vars_set": env_keys,
        "has_credentials_file": cred_file_exists,
        "has_config_file": config_file_exists,
        "region": get_aws_region()
    }


def check_bedrock_access() -> Dict[str, Any]:
    """
    Check Amazon Bedrock availability, caller identity, and model access.
    Handles all AWS exceptions and returns actionable diagnostics.
    """
    region = get_aws_region()
    model_id = get_bedrock_model_id()
    safe_creds = check_aws_credentials_safe()

    result = {
        "configured": False,
        "region": region,
        "model_id": model_id,
        "auth_method": safe_creds["auth_method"],
        "account_id": None,
        "arn": None,
        "model_accessible": False,
        "error_type": None,
        "error_message": None,
        "remediation": None
    }

    if not safe_creds["configured"]:
        result["error_type"] = "NoCredentialsError"
        result["error_message"] = "No AWS credentials located in environment, .env file, or ~/.aws/credentials."
        result["remediation"] = (
            "Configure AWS credentials by copying .env.example to .env and filling in your "
            "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION, or by running 'aws configure'."
        )
        return result

    # Test STS get-caller-identity
    try:
        session = boto3.Session(region_name=region)
        sts = session.client("sts", region_name=region)
        caller = sts.get_caller_identity()
        result["configured"] = True
        result["arn"] = caller.get("Arn")
        # Mask account ID for privacy
        raw_acct = str(caller.get("Account", ""))
        result["account_id"] = f"***{raw_acct[-4:]}" if len(raw_acct) >= 4 else "***"
    except botocore.exceptions.NoCredentialsError:
        result["error_type"] = "NoCredentialsError"
        result["error_message"] = "AWS credentials were not found or could not be loaded."
        result["remediation"] = "Verify that AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are valid in .env."
        return result
    except botocore.exceptions.ClientError as e:
        code = e.response.get("Error", {}).get("Code", "ClientError")
        result["error_type"] = code
        result["error_message"] = f"STS authentication failed ({code}): {e.response.get('Error', {}).get('Message')}"
        result["remediation"] = "Check that your AWS credentials are valid and active."
        return result
    except Exception as e:
        result["error_type"] = type(e).__name__
        result["error_message"] = f"AWS connection error: {str(e)}"
        result["remediation"] = "Check network connectivity to AWS endpoints."
        return result

    # Test Bedrock Client connectivity
    try:
        bedrock = session.client("bedrock", region_name=region)
        # Attempt to list foundation models (tests bedrock:ListFoundationModels)
        response = bedrock.list_foundation_models(byProvider="Anthropic")
        models = [m.get("modelId") for m in response.get("modelSummaries", [])]
        
        result["model_accessible"] = any(model_id in m for m in models) or len(models) > 0
        if not result["model_accessible"]:
            result["remediation"] = (
                f"Model '{model_id}' was not returned in bedrock:ListFoundationModels for region '{region}'. "
                f"Ensure Bedrock Model Access is enabled in the AWS Bedrock Console for Anthropic Claude models."
            )
    except botocore.exceptions.ClientError as e:
        code = e.response.get("Error", {}).get("Code", "ClientError")
        result["error_type"] = code
        result["error_message"] = f"Bedrock client error ({code}): {e.response.get('Error', {}).get('Message')}"
        if code == "AccessDeniedException":
            result["remediation"] = (
                "IAM policy lacks 'bedrock:ListFoundationModels' or 'bedrock:InvokeModel' permissions, "
                "or Anthropic Claude model access has not been requested in the AWS Bedrock Console."
            )
        else:
            result["remediation"] = f"Review AWS error code: {code}."
    except Exception as e:
        result["error_type"] = type(e).__name__
        result["error_message"] = f"Bedrock inspection failed: {str(e)}"
        result["remediation"] = "Verify Bedrock is supported in your configured region."

    return result


def get_iam_policy_template() -> Dict[str, Any]:
    """
    Return the least-privilege IAM policy document required for FarmGuard AI.
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "FarmGuardBedrockModelAccess",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-*",
                    "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-*",
                    "arn:aws:bedrock:*::foundation-model/amazon.nova-*"
                ]
            },
            {
                "Sid": "FarmGuardBedrockDiscovery",
                "Effect": "Allow",
                "Action": [
                    "bedrock:ListFoundationModels",
                    "bedrock:GetFoundationModel"
                ],
                "Resource": "*"
            }
        ]
    }

