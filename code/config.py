"""
Antigravity Configuration Module.

Pure generic configuration for the Financial Digital Twin and Counterfactual Planning Engine.
Guaranteed zero-hardcoded dataset references.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any


@dataclass
class ModelConfig:
    host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "gemma3:4b"))
    timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT", "30.0"))
    enable_cache: bool = True
    cache_dir: Path = field(default_factory=lambda: Path(".cache/model_cache"))
    cost_per_1k_input_tokens: float = 0.0001   # Estimated nominal cost for local/benchmark tracking
    cost_per_1k_output_tokens: float = 0.0002


@dataclass
class SimulationConfig:
    forecast_days: int = 90
    max_spending_interventions: int = 3
    default_home_currency: str = "USD"
    strict_verification: bool = True
    max_repair_iterations: int = 5


@dataclass
class PathConfig:
    base_dir: Path = field(default_factory=lambda: Path(os.getcwd()))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATASET_DIR", "data")))
    output_file: Path = field(default_factory=lambda: Path(os.getenv("OUTPUT_PATH", "output.csv")))
    decision_cards_file: Path = field(default_factory=lambda: Path("decision_cards.json"))
    usage_report_file: Path = field(default_factory=lambda: Path("evaluation/usage_report.md"))


@dataclass
class AppConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    paths: PathConfig = field(default_factory=PathConfig)


# Global default configuration instance
CONFIG = AppConfig()
