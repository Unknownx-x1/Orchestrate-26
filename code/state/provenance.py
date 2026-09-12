"""
Evidence Provenance and Lineage Module.
Tracks the exact origin, timestamp, source ID, and confidence for every material fact.
"""

from __future__ import annotations
import uuid
import datetime
from dataclasses import dataclass, field
from typing import Optional, Any, Dict


@dataclass
class ProvenanceRecord:
    source_type: str  # 'csv', 'message', 'image_ocr', 'model_extraction', 'rule'
    source_id: str    # e.g., filename, event_id, image_id, message_id
    effective_date: Optional[str] = None
    confidence: float = 1.0
    rationale: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "effective_date": self.effective_date,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "created_at": self.created_at
        }


@dataclass
class EvidenceFact:
    fact_id: str = field(default_factory=lambda: f"fact_{uuid.uuid4().hex[:8]}")
    entity_type: str = "event"  # 'user', 'request', 'event', 'transaction'
    entity_id: str = ""
    field_name: str = ""
    value: Any = None
    provenance: Optional[ProvenanceRecord] = None
    status: str = "active"  # 'active', 'cancelled', 'amended', 'settled'
    superseded_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "field_name": self.field_name,
            "value": self.value,
            "status": self.status,
            "superseded_by": self.superseded_by,
            "provenance": self.provenance.to_dict() if self.provenance else None
        }
