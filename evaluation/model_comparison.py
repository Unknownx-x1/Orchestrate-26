"""
Model Benchmarking & Comparison Suite.
Compares extraction latency, token totals, and reliability across different local Ollama models.
"""

from __future__ import annotations
import time
import logging
from typing import List, Dict, Any
from code.intelligence.ollama_gemma import OllamaGemmaAdapter

logger = logging.getLogger(__name__)

BENCHMARK_PROMPTS = [
    "User note: 'Need to pay $450 rent by next Friday. I can do half today if needed.' Output JSON: {\"intent\": ..., \"allow_partial\": ...}",
    "Message: 'Notification: Your subscription of $29.99 has been cancelled effective immediately.' Output JSON: {\"action\": ..., \"amount\": ...}",
    "Explanation request: 'Request req_1: Approved via installment. Total $300. Binding constraint: none.' Output 1 sentence summary."
]


def benchmark_model(model_name: str, runs: int = 2) -> Dict[str, Any]:
    adapter = OllamaGemmaAdapter(model=model_name)
    latencies = []

    print(f"\n--- Benchmarking Model: {model_name} ---")
    for i in range(runs):
        for idx, prompt in enumerate(BENCHMARK_PROMPTS):
            t0 = time.time()
            resp = adapter.generate(prompt=prompt, system="You are a benchmarking assistant. Be concise.")
            dur = time.time() - t0
            latencies.append(dur)
            print(f"  Run {i+1}, Prompt {idx+1}: {dur:.3f}s, Response length: {len(resp)} chars")

    usage = adapter.get_usage_summary()
    usage["avg_latency_sec"] = round(sum(latencies) / max(len(latencies), 1), 3)
    return usage


def main():
    models = ["gemma3:4b"]
    results = {}
    for m in models:
        try:
            results[m] = benchmark_model(m, runs=1)
        except Exception as e:
            print(f"Failed to benchmark {m}: {e}")

    print("\n================ BENCHMARK COMPARISON SUMMARY ================")
    for m, stat in results.items():
        print(f"Model: {m}")
        print(f"  Total Calls: {stat.get('total_calls')}")
        print(f"  Total Tokens: {stat.get('total_tokens')}")
        print(f"  Avg Latency: {stat.get('avg_latency_sec')}s")
        print(f"  Est Cost: ${stat.get('estimated_cost_usd'):.5f}")
    print("================================================================")


if __name__ == "__main__":
    main()
