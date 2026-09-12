# Financial Digital Twin & Counterfactual Planning Engine

> **Gemma 4:2B + Ollama Edition | Build Specification Implementation**

---

## 1. The Winning Thesis

Affordability is a **constrained temporal simulation problem**, not an LLM generative question. Models are uniquely suited for interpreting unstructured human language, invoices, and conflicting evidence; deterministic software reconstructs the user's financial state, simulates counterfactual cash flows, enforces invariant constraints, ranks viable payment plans, and independently certifies safety.

```
Evidence ──> Financial Twin ──> Temporal Futures ──> Candidate Plans ──> Optimization ──> Independent Proof ──> Explanation
```

---

## 2. 30-Second AI Judge Defense

> *"We treated affordability as a constrained temporal decision problem, not an LLM question. Our agent reconstructs a user's financial digital twin from structured, textual, and visual evidence, generates counterfactual payment futures, searches for plans that satisfy financial and preference constraints, and independently verifies every recommendation across a 90-day simulation. Models handle ambiguity; deterministic systems decide and certify the money."*

### Core Architectural Differentiators
1. **Zero-Hardcoding Architecture**: Every row, ID, amount, and option is discovered dynamically at runtime. Replacing the dataset with another structurally compatible dataset runs completely unchanged.
2. **Evidence Firewall**: External messages, receipts, and images are strictly untrusted data. Embedded instructions or prompt injections are neutralized and cannot alter system rules or arithmetic.
3. **Deterministic Financial Physics**: Evaluates daily cash flows over a 90-day horizon:
   ```
   balance[t] = balance[t-1] + confirmed_inflows[t] - protected_outflows[t] - candidate_payments[t]
   ```
   Ensuring: `min(balance[t]) >= minimum_balance_to_keep` for every forecast day `t` in `[0, 90]`.
4. **Algorithmic Binary Search**: Calculates the exact `amount_safe_to_pay` today via binary search on `[0, requested_amount]` rather than guessing.
5. **Spending Interventions**: Formally models flexible recurring expenses as explicit adjustments (`stop:<event_id>`, `reduce_to:<event_id>:<new_amount>`), searching for the minimal changes needed to restore safety (max 3, mutual exclusion enforced).
6. **Independent Safety Verifier + Repair Loop**: Certified by an isolated certifying simulator clone before output generation. The model never certifies its own decisions.

---

## 3. Repository Structure

```
orchestrate'26/
├── code/
│   ├── app.py                      # Master 20-step runtime pipeline
│   ├── config.py                   # Pure dynamic configuration
│   ├── ingest/                     # CSV discovery, media discovery, joins, schema validator
│   ├── intelligence/               # Ollama adapter, request parser, message interpreter, evidence firewall
│   ├── state/                      # Provenance, conflict resolver, evidence graph, financial twin
│   ├── simulation/                 # FX engine, event expander, cashflow timeline, physics simulator
│   ├── planning/                   # Candidate generator, binary search optimizer, plan ranker
│   ├── verification/               # Invariants, independent verifier, repair loop
│   └── output/                     # Output schema validator, CSV writer, decision cards
├── evaluation/
│   ├── evaluate.py                 # Master test scorecard runner
│   ├── validators.py               # Invariant validation utilities
│   ├── simulator_tests.py          # Temporal physics unit tests
│   ├── adversarial_tests.py        # Prompt injection & precedence tests
│   ├── regression_tests.py         # End-to-end determinism tests
│   ├── model_comparison.py         # Latency, token, & cost benchmarking
│   └── usage_report.md             # Auto-generated telemetry report
├── prompts/                        # System prompt contracts
├── audit/
│   └── static_audit.py             # Mandatory pre-submission anti-hardcoding linter
└── README.md
```

---

## 4. Quick Start

### Requirements
- Python 3.10+ (tested on Python 3.13)
- Ollama with `gemma3:4b` running locally: `ollama run gemma3:4b`

### Run Anti-Hardcoding Static Audit
```bash
python audit/static_audit.py
```

### Run Master Evaluation Suite
```bash
python evaluation/evaluate.py
```

### Run End-to-End Pipeline
```bash
python code/app.py --data-dir fixtures/demo_dataset --output output.csv
```

---

## 5. Non-Negotiable Hard Invariants

- **Zero Hardcoded IDs/Constants**: Verified by static AST/regex audit script.
- **Strict Evidence Precedence**:
  1. Explicit cancellation/amendment
  2. Newer same-source record
  3. Settled event over estimate
  4. Financially conservative tie-breaker
- **Missing Amounts**: Resolved from linked media evidence; never converted to zero.
- **Earliest Safe Full-Payment Date**: Computed independently of payment method preference.
- **Chronological Payments & Arithmetic**: Sum of schedule payments equals total declared.
- **Verified Explanations**: Generated exclusively from verified facts after freezing the decision.
