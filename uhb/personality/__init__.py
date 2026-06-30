"""Behavioral fingerprinting — measure HOW a model operates, not just how accurate it is."""

from .metrics import PersonalityMetrics
from .fingerprint import PersonalityFingerprint, generate_fingerprint

__version__ = "0.1.0"
__all__ = ["PersonalityMetrics", "PersonalityFingerprint", "generate_fingerprint"]
