# Evaluation Harness & Verification Suite

This evaluation suite enforces reliability, invariant compliance, and adversarial robustness for the Antigravity Financial Decision Engine.

## Structure
- `evaluate.py`: Master test runner executing all suites and printing a unified scorecard.
- `simulator_tests.py`: Validates 90-day cash flow physics, monotonic binary search, recurrence math, and FX conversion.
- `adversarial_tests.py`: Validates defense against prompt injections, conflicting records, blank amount image handling, and unsafe installment traps.
- `regression_tests.py`: Ensures pipeline runs deterministically and produces valid schemas.
- `model_comparison.py`: Benchmarks Ollama latency, token totals, and estimated cost.
- `validators.py`: Reusable invariant assertions.

## Running Evaluations
```bash
python evaluation/evaluate.py
```
