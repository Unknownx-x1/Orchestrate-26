"""
Output CSV and Decision Card Writer.
Produces verified output.csv and rich decision_cards.json traces.
Generates concise post-verification explanations via Gemma from verified facts only.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from code.output.schema_validator import OutputValidator
from code.intelligence.ollama_gemma import OllamaGemmaAdapter

logger = logging.getLogger(__name__)


class OutputWriter:
    """
    Serializes verified financial decisions to output.csv and decision_cards.json.
    """

    def __init__(self, adapter: Optional[OllamaGemmaAdapter] = None):
        self.adapter = adapter or OllamaGemmaAdapter()

    def generate_explanation(
        self,
        request_id: str,
        status: str,
        method: str,
        total_paid: float,
        binding_constraints: List[str],
        spending_interventions: List[str]
    ) -> str:
        """
        Generates explanation strictly from verified facts.
        Explanation cannot alter the decision.
        """
        facts_summary = (
            f"Request: {request_id}, Status: {status}, Method: {method}, "
            f"Total Paid: ${total_paid:.2f}, Constraints: {', '.join(binding_constraints) or 'None'}, "
            f"Interventions: {', '.join(spending_interventions) or 'None'}"
        )

        prompt = (
            f"Based STRICTLY on these verified financial facts, write a concise 1-2 sentence explanation:\n"
            f"{facts_summary}\n"
            f"Do not invent facts or alter any figures."
        )

        response = self.adapter.generate(
            prompt=prompt,
            system="You are a concise financial compliance assistant summarizing certified decisions.",
            temperature=0.2
        )

        cleaned = response.strip().replace("\n", " ")
        if not cleaned or len(cleaned) < 10:
            # Deterministic fallback summary
            if status == "APPROVED":
                cleaned = f"Approved for payment via {method} satisfying 90-day minimum balance reserve."
            elif status == "MODIFIED":
                cleaned = f"Approved with {len(spending_interventions)} spending adjustment(s) to protect minimum balance reserve."
            else:
                cleaned = f"Unable to approve request without violating minimum balance reserve ({', '.join(binding_constraints)})."

        return cleaned

    def write_output_csv(self, rows: List[Dict[str, Any]], output_path: str | Path):
        """
        Validates rows against hard invariants and saves to CSV.
        """
        OutputValidator.validate_rows(rows)
        df = pd.DataFrame(rows)
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_file, index=False)
        logger.info(f"Successfully wrote {len(rows)} verified decisions to {out_file}.")

    def write_decision_cards(self, cards: List[Dict[str, Any]], cards_path: str | Path):
        """
        Persists internal decision traces for audit and AI Judge defense.
        """
        cards_file = Path(cards_path)
        cards_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cards_file, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2)
        logger.info(f"Successfully wrote {len(cards)} decision cards to {cards_file}.")
