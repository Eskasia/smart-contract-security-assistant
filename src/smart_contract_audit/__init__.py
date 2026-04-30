"""Smart contract security assistant."""

from .analyzer import analyze_contract
from .models import AnalysisReport, Finding, Location, RagChunk

__all__ = [
    "AnalysisReport",
    "Finding",
    "Location",
    "RagChunk",
    "analyze_contract",
]

__version__ = "0.1.0"
