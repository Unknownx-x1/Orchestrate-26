"""
Generic Deterministic Conflict Resolution Engine.
Implements the 4-tier precedence hierarchy defined in Section 6 of the build specification.
Strictly generic: zero event-specific or hardcoded rules.
"""

from __future__ import annotations
import logging
from typing import List, Optional
from code.state.provenance import EvidenceFact

logger = logging.getLogger(__name__)


class ConflictResolver:
    """
    Resolves conflicting evidence facts based on:
    1. Explicit cancellation / settlement / amendment
    2. Newer same-source record (by timestamp)
    3. Settled event over estimate/forecast
    4. Financially safer interpretation if still unresolved
    """

    @classmethod
    def resolve_facts(cls, facts: List[EvidenceFact], is_outflow: bool = True) -> EvidenceFact:
        """
        Takes a list of competing facts for the same entity and field,
        and resolves to the single winning fact according to generic precedence.
        """
        if not facts:
            raise ValueError("Cannot resolve empty list of facts.")
        if len(facts) == 1:
            return facts[0]

        # Tier 1: Check for explicit cancellation, settlement, or amendment
        cancelled_or_amended = [
            f for f in facts 
            if f.status in {"cancelled", "amended", "settled"}
        ]
        if cancelled_or_amended:
            # If multiple amendments/settlements, sort by effective date / creation
            sorted_tier1 = sorted(
                cancelled_or_amended, 
                key=lambda x: (x.provenance.effective_date or x.provenance.created_at if x.provenance else ""),
                reverse=True
            )
            winner = sorted_tier1[0]
            logger.debug(f"Tier 1 win for {winner.fact_id} (status: {winner.status})")
            return winner

        # Tier 2: Check for same-source with strictly newer date
        source_grouped = {}
        for f in facts:
            sid = f.provenance.source_id if (f.provenance and f.provenance.source_id) else f.fact_id
            source_grouped.setdefault(sid, []).append(f)

        newest_candidates = []
        for sid, flist in source_grouped.items():
            if len(flist) > 1:
                # Keep strictly newest record from this same source
                sorted_flist = sorted(
                    flist,
                    key=lambda x: (x.provenance.effective_date or x.provenance.created_at if x.provenance else ""),
                    reverse=True
                )
                newest_candidates.append(sorted_flist[0])
            else:
                newest_candidates.append(flist[0])

        # If only one candidate remains after same-source pruning, return it
        if len(newest_candidates) == 1:
            return newest_candidates[0]

        # Tier 3: Check for settled over estimate/forecast
        settled_candidates = [
            f for f in newest_candidates 
            if f.provenance and "settled" in (f.provenance.rationale or "").lower()
        ]
        if settled_candidates:
            return settled_candidates[0]

        # Tier 4: Financially safer interpretation if still unresolved
        # For an outflow/expense, larger amount is safer (more conservative).
        # For an inflow/income, smaller amount is safer (more conservative).
        try:
            numeric_facts = [(f, float(f.value)) for f in newest_candidates if f.value is not None]
            if numeric_facts:
                if is_outflow:
                    # Maximize outflow
                    winner, val = max(numeric_facts, key=lambda pair: pair[1])
                else:
                    # Minimize inflow
                    winner, val = min(numeric_facts, key=lambda pair: pair[1])
                winner.provenance.rationale += " [Resolved via Tier 4: financially conservative safety tie-break]"
                return winner
        except (ValueError, TypeError):
            pass

        # Fallback: Highest confidence
        return max(newest_candidates, key=lambda x: x.provenance.confidence if x.provenance else 0.0)
