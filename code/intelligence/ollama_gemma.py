"""
Ollama Gemma Interface & Cost Tracking Adapter.
Handles prompt execution, caching by content hash, token accounting,
and robust fallback extraction.
"""

from __future__ import annotations
import os
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from code.config import CONFIG

logger = logging.getLogger(__name__)


class OllamaGemmaAdapter:
    """
    Adapter for local Gemma model via Ollama.
    Tracks all calls, logs tokens, caches by content hash, and provides
    safe deterministic fallbacks if the local daemon is unreachable.
    """

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host or CONFIG.model.host
        self.model = model or CONFIG.model.model
        self.cache_dir = CONFIG.model.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Call & token telemetry
        self.total_calls = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.call_history: List[Dict[str, Any]] = []

    def _hash_key(self, prompt: str, system: str = "") -> str:
        content = f"{self.model}:{system}:{prompt}".encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def generate(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        """
        Executes generation against Ollama with caching and token accounting.
        """
        cache_key = self._hash_key(prompt, system)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if CONFIG.model.enable_cache and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    logger.debug(f"Cache hit for prompt hash {cache_key[:8]}")
                    return cached.get("response", "")
            except Exception:
                pass

        self.total_calls += 1
        start_t = time.time()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 512
            }
        }

        response_text = ""
        prompt_tokens = len(prompt.split()) * 2  # Estimate if not provided
        completion_tokens = 0

        try:
            url = f"{self.host.rstrip('/')}/api/generate"
            r = requests.post(url, json=payload, timeout=CONFIG.model.timeout_seconds)
            if r.status_code == 200:
                data = r.json()
                response_text = data.get("response", "")
                prompt_tokens = data.get("prompt_eval_count", prompt_tokens)
                completion_tokens = data.get("eval_count", len(response_text.split()) * 2)
            else:
                logger.warning(f"Ollama returned HTTP {r.status_code}: {r.text}")
        except Exception as e:
            logger.warning(f"Ollama call failed or timed out: {e}. Utilizing fallback extractor.")
            response_text = ""

        duration = time.time() - start_t
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        record = {
            "model": self.model,
            "call_index": self.total_calls,
            "duration_sec": round(duration, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cache_key": cache_key
        }
        self.call_history.append(record)

        # Write to cache
        if CONFIG.model.enable_cache and response_text:
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump({"response": response_text, "record": record}, f)
            except Exception:
                pass

        return response_text

    def get_usage_summary(self) -> Dict[str, Any]:
        cost_in = (self.total_prompt_tokens / 1000.0) * CONFIG.model.cost_per_1k_input_tokens
        cost_out = (self.total_completion_tokens / 1000.0) * CONFIG.model.cost_per_1k_output_tokens
        avg_tokens = (
            (self.total_prompt_tokens + self.total_completion_tokens) / max(self.total_calls, 1)
        )
        return {
            "model_name": self.model,
            "total_calls": self.total_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "average_tokens_per_call": round(avg_tokens, 1),
            "estimated_cost_usd": round(cost_in + cost_out, 5)
        }
