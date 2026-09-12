# LLM & Resource Usage Report

Generated: 2026-09-12T18:51:05.562719+00:00

## Model Execution Telemetry
- **Model Name**: `gemma3:4b`
- **Total API Calls**: 420
- **Total Prompt Tokens**: 46717
- **Total Completion Tokens**: 14693
- **Total Combined Tokens**: 61410
- **Average Tokens / Call**: 146.2
- **Estimated Operational Cost**: $0.00761 USD

## Architectural Guardrails Observed
- Language models are restricted strictly to semantic extraction and post-verification explanation.
- Deterministic Python handles 100% of arithmetic, simulation, binary search, and verification.
- Evidence Firewall isolated all untrusted message and image input.
- Strict zero-hardcoding guarantee: all IDs, amounts, and options discovered at runtime.
