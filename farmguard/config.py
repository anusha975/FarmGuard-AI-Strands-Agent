"""
FarmGuard AI configuration and environment settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load local .env file if available
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "FarmGuard AI"
    VERSION: str = "1.0.0"
    
    # Mode: 'live' or 'simulation'
    FARMGARD_MODE: str = os.getenv("FARMGARD_MODE", "simulation").lower()
    
    # AWS Bedrock settings
    AWS_REGION: str = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_SESSION_TOKEN: str = os.getenv("AWS_SESSION_TOKEN", "")
    
    # Default Bedrock Model: Anthropic Claude 3.5 Sonnet v1
    BEDROCK_MODEL_ID: str = os.getenv(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    
    # Open-Meteo Weather API (Free open-source agro-meteorology API, no API key required)
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    
    @classmethod
    def is_aws_configured(cls) -> bool:
        """Check if AWS credentials or profiles are available."""
        # 1. Direct environment variables
        if cls.AWS_ACCESS_KEY_ID and cls.AWS_SECRET_ACCESS_KEY:
            return True
        # 2. AWS Profile or default ~/.aws/credentials
        aws_dir = Path.home() / ".aws"
        if (aws_dir / "credentials").exists() or (aws_dir / "config").exists():
            return True
        return False

settings = Settings()
