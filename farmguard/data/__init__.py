"""Data package initialization."""
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES
from farmguard.data.telugu_translations import (
    TELUGU_CROPS,
    TELUGU_SOILS,
    TELUGU_STAGES,
    TELUGU_RISK_LEVELS,
    TELUGU_HAZARDS,
    TELUGU_COMMON_ADVICE
)

__all__ = [
    "CROP_DATABASE",
    "SOIL_PROPERTIES",
    "TELUGU_CROPS",
    "TELUGU_SOILS",
    "TELUGU_STAGES",
    "TELUGU_RISK_LEVELS",
    "TELUGU_HAZARDS",
    "TELUGU_COMMON_ADVICE",
]
