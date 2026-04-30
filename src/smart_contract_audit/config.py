from __future__ import annotations

from dataclasses import dataclass

DETECTOR_MAPPING: dict[str, tuple[str, int, list[str]]] = {
    "reentrancy-eth": ("reentrancy", 3, ["SWC-107"]),
    "reentrancy-no-eth": ("reentrancy", 2, ["SWC-107"]),
    "reentrancy-benign": ("reentrancy", 1, ["SWC-107"]),
    "unprotected-upgrade": ("access_control", 3, ["SWC-105"]),
    "suicidal": ("access_control", 3, ["SWC-106"]),
    "arbitrary-send-eth": ("access_control", 3, ["SWC-105"]),
    "unchecked-lowlevel": ("unchecked_external_call", 2, ["SWC-104"]),
    "unchecked-send": ("unchecked_external_call", 2, ["SWC-104"]),
    "controlled-delegatecall": ("dangerous_delegatecall", 3, ["SWC-112"]),
    "delegatecall-loop": ("dangerous_delegatecall", 2, ["SWC-112"]),
    "controlled-array-length": ("array_length_manipulation", 2, ["Slither-specific"]),
}

SUPPORTED_DETECTORS = tuple(DETECTOR_MAPPING)
SUPPORTED_SOLIDITY_MINOR_RANGE = ("0.6", "0.7", "0.8")
BUSINESS_LOGIC_KEYWORDS = ("reward", "oracle", "pool", "swap", "staking")


@dataclass(frozen=True)
class RagModeConfig:
    bm25_top_k: int
    dense_top_k: int
    rerank_input_limit: int
    output_top_k: int
    dense_enabled: bool = True


RAG_MODES: dict[str, RagModeConfig] = {
    "quality": RagModeConfig(50, 50, 100, 5),
    "balanced": RagModeConfig(30, 30, 60, 3),
    "fast": RagModeConfig(20, 20, 40, 3),
    "fallback": RagModeConfig(20, 0, 20, 3, dense_enabled=False),
}

DEFAULT_DATASET_VERSION = "dataset_v1.0"
DEFAULT_MODEL_VERSION = "mlx-8b-4bit"
DEFAULT_RAG_MODE = "balanced"
MAX_SOLIDITY_LINES = 500
