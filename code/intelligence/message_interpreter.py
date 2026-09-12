"""
Message Interpreter Module.
Extracts financial amendments, cancellations, confirmations, and delays from unstructured messages.
Treats all messages as untrusted evidence via the Evidence Firewall.
"""

from __future__ import annotations
import json
import re
import logging
from typing import Dict, Any, Optional
from code.intelligence.ollama_gemma import OllamaGemmaAdapter
from code.intelligence.evidence_firewall import EvidenceFirewall
from code.state.provenance import EvidenceFact, ProvenanceRecord

logger = logging.getLogger(__name__)


class MessageInterpreter:
    """
    Extracts semantic facts from messages:
    - Cancellation of pending transactions/bills
    - Amendments of recurring costs or salaries
    - Payment delays and confirmations
    """

    def __init__(self, adapter: OllamaGemmaAdapter, firewall: Optional[EvidenceFirewall] = None):
        self.adapter = adapter
        self.firewall = firewall or EvidenceFirewall()

    def interpret_message(self, message_record: Dict[str, Any]) -> Optional[EvidenceFact]:
        clean_msg = self.firewall.inspect_and_filter(message_record)
        msg_id = str(clean_msg.get("message_id", clean_msg.get("id", "msg_unknown")))
        body = str(clean_msg.get("body", clean_msg.get("text", clean_msg.get("message", ""))))
        target_event_id = str(clean_msg.get("event_id", clean_msg.get("related_event_id", "")))
        timestamp = str(clean_msg.get("timestamp", clean_msg.get("date", "")))

        if not body:
            return None

        # Deterministic regex heuristics for common financial signals
        action = "none"
        new_amount = None
        
        lower_body = body.lower()
        if any(w in lower_body for w in ["cancel", "cancelled", "terminate", "revoked", "stopped", "void"]):
            action = "cancellation"
        elif any(w in lower_body for w in ["settled", "paid off", "cleared"]):
            action = "settled"
        elif any(w in lower_body for w in ["increase", "reduced", "discount", "amended", "updated amount"]):
            action = "amendment"
            amt_match = re.search(r"(\$|€|£|₹)?\s*(\d+(\.\d{1,2})?)", body)
            if amt_match:
                new_amount = float(amt_match.group(2))

        # Query Gemma for deeper contextual disambiguation if ambiguous
        if action == "none" and len(body.split()) > 4:
            prompt = (
                f"Analyze this financial notification and output ONLY JSON:\n"
                f"Notification: {body}\n\n"
                f'Contract: {{"action": "cancellation|settlement|amendment|delay|none", "new_amount": float or null, "event_reference": "id or null"}}'
            )
            response = self.adapter.generate(prompt=prompt, system="You extract financial message actions into strict JSON.")
            try:
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    action = parsed.get("action", action)
                    if parsed.get("new_amount"):
                        new_amount = float(parsed["new_amount"])
                    if not target_event_id and parsed.get("event_reference"):
                        target_event_id = str(parsed["event_reference"])
            except Exception:
                pass

        if action in {"cancellation", "settled"}:
            status = "cancelled" if action == "cancellation" else "settled"
            return EvidenceFact(
                entity_type="event",
                entity_id=target_event_id or msg_id,
                field_name="status",
                value=status,
                status=status,
                provenance=ProvenanceRecord(
                    source_type="message",
                    source_id=msg_id,
                    effective_date=timestamp,
                    confidence=0.95,
                    rationale=f"Message indicated {action}"
                )
            )
        elif action == "amendment" and new_amount is not None:
            return EvidenceFact(
                entity_type="event",
                entity_id=target_event_id or msg_id,
                field_name="amount",
                value=new_amount,
                status="amended",
                provenance=ProvenanceRecord(
                    source_type="message",
                    source_id=msg_id,
                    effective_date=timestamp,
                    confidence=0.90,
                    rationale=f"Message amended amount to {new_amount}"
                )
            )

        return None
