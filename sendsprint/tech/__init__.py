"""Tech detection: fingerprint a repo's stack(s) from filesystem markers."""

from .detector import TechFingerprint, detect_tech

__all__ = ["TechFingerprint", "detect_tech"]
