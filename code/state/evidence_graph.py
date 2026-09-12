"""
Evidence Graph Module.
Constructs a unified, date-stamped bipartite/multi-relational graph linking
users, requests, events, messages, and image evidence.
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any, Optional, Set
from code.state.provenance import EvidenceFact, ProvenanceRecord
from code.state.conflict_resolver import ConflictResolver

logger = logging.getLogger(__name__)


class EvidenceGraph:
    """
    Maintains relational evidence links and resolves field-level facts.
    """

    def __init__(self):
        # Nodes
        self.users: Dict[str, Dict[str, Any]] = {}
        self.requests: Dict[str, Dict[str, Any]] = {}
        self.events: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, Dict[str, Any]] = {}
        self.images: Dict[str, Dict[str, Any]] = {}

        # Edges
        self.user_to_requests: Dict[str, Set[str]] = {}
        self.user_to_events: Dict[str, Set[str]] = {}
        self.event_to_messages: Dict[str, Set[str]] = {}
        self.event_to_images: Dict[str, Set[str]] = {}
        self.request_to_messages: Dict[str, Set[str]] = {}
        self.event_parent_child: Dict[str, Set[str]] = {}

        # Fact repository: (entity_id, field_name) -> List[EvidenceFact]
        self.field_facts: Dict[tuple[str, str], List[EvidenceFact]] = {}

    def add_user(self, user_id: str, data: Dict[str, Any]):
        self.users[str(user_id)] = data

    def add_request(self, request_id: str, user_id: str, data: Dict[str, Any]):
        rid = str(request_id)
        uid = str(user_id)
        self.requests[rid] = data
        self.user_to_requests.setdefault(uid, set()).add(rid)

    def add_event(self, event_id: str, user_id: str, data: Dict[str, Any], related_event_id: Optional[str] = None):
        eid = str(event_id)
        uid = str(user_id)
        self.events[eid] = data
        self.user_to_events.setdefault(uid, set()).add(eid)
        if related_event_id:
            parent_id = str(related_event_id)
            self.event_parent_child.setdefault(parent_id, set()).add(eid)

    def add_message(self, message_id: str, data: Dict[str, Any], request_id: Optional[str] = None, event_id: Optional[str] = None):
        mid = str(message_id)
        self.messages[mid] = data
        if request_id:
            self.request_to_messages.setdefault(str(request_id), set()).add(mid)
        if event_id:
            self.event_to_messages.setdefault(str(event_id), set()).add(mid)

    def link_image_to_event(self, event_id: str, image_id: str, metadata: Optional[Dict[str, Any]] = None):
        eid = str(event_id)
        iid = str(image_id)
        self.images[iid] = metadata or {}
        self.event_to_images.setdefault(eid, set()).add(iid)

    def record_fact(self, fact: EvidenceFact):
        key = (str(fact.entity_id), str(fact.field_name))
        self.field_facts.setdefault(key, []).append(fact)

    def get_resolved_field(self, entity_id: str, field_name: str, is_outflow: bool = True) -> Optional[EvidenceFact]:
        """
        Retrieves the single winner fact after applying deterministic conflict resolution.
        """
        key = (str(entity_id), str(field_name))
        facts = self.field_facts.get(key, [])
        if not facts:
            return None
        return ConflictResolver.resolve_facts(facts, is_outflow=is_outflow)

    def get_linked_evidence_for_request(self, request_id: str) -> List[str]:
        """Returns list of message and image IDs linked directly or via user/events."""
        rid = str(request_id)
        evidence = set(self.request_to_messages.get(rid, set()))
        return sorted(list(evidence))
