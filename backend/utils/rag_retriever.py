"""
RAG Retriever — PetCare Illness Knowledge Base
Authors: Syed Ali Turab | Team: Broadview
Date: March 8, 2026

Lightweight keyword-overlap retrieval for grounding triage LLM calls with
evidence-based illness reference data from pet_illness_kb.json.

Design decision: No vector DB or embeddings required for POC.
  - Keyword overlap scoring is fast (<1ms), dependency-free, and deterministic.
  - Retrieval is grounded in curated clinical keywords (not user phrasing alone).
  - Top-k results are formatted as a concise reference block for the LLM prompt.

Scoring:
  1. Tokenise query (lowercase, split on whitespace/punctuation).
  2. For each illness entry, count how many of its keywords appear in the query.
  3. Species bonus: +2 if species field matches query species.
  4. Category bonus: +1 if category appears in query text.
  5. Return top-k entries sorted by score descending (minimum score threshold: 1).
"""

import json
import os
import re
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger('petcare.utils.rag_retriever')

_KB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'pet_illness_kb.json')

# ── Tokeniser ──────────────────────────────────────────────────────────────────
_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _tokenise(text: str) -> set:
    return set(_TOKEN_RE.findall(text.lower()))


# ── Load KB once ───────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _load_kb() -> list:
    """Load and cache the illness knowledge base."""
    try:
        with open(os.path.abspath(_KB_PATH), 'r', encoding='utf-8') as f:
            data = json.load(f)
        entries = data.get('illnesses', [])
        logger.info(f"RAG KB loaded: {len(entries)} illness entries")
        return entries
    except Exception as e:
        logger.error(f"Failed to load illness KB: {e}")
        return []


# ── Scoring ────────────────────────────────────────────────────────────────────
def _score_entry(entry: dict, query_tokens: set, species: str, query_lower: str) -> int:
    """
    Score one KB entry against the query.

    Returns an integer relevance score (0 = not relevant).
    """
    score = 0

    # Keyword overlap (each matched keyword = 1 point)
    keywords = entry.get('keywords', [])
    for kw in keywords:
        kw_tokens = _tokenise(kw)
        # Match if all tokens of the keyword phrase appear in the query
        if kw_tokens and kw_tokens.issubset(query_tokens):
            score += 1

    if score == 0:
        return 0  # No keyword match → skip species/category bonuses

    # Species match bonus
    if species:
        sp_lower = species.lower().strip()
        entry_species = [s.lower() for s in entry.get('species', [])]
        if sp_lower in entry_species or any(sp_lower.startswith(s) for s in entry_species):
            score += 2

    # Category match bonus
    category = entry.get('category', '').lower()
    if category and category in query_lower:
        score += 1

    return score


# ── Public API ─────────────────────────────────────────────────────────────────
def retrieve_illness_context(
    complaint: str,
    species: str = '',
    top_k: int = 3,
    min_score: int = 1
) -> list[dict]:
    """
    Retrieve the top-k illness KB entries most relevant to the complaint.

    Args:
        complaint: Chief complaint text (free-form user description).
        species:   Detected species (e.g. 'dog', 'cat'). Used for scoring bonus.
        top_k:     Maximum number of results to return.
        min_score: Minimum relevance score to include a result.

    Returns:
        List of dicts, each containing:
          - name, category, typical_urgency, urgency_escalators,
            key_triage_notes, red_flags, species_notes (for matched species only)
    """
    if not complaint:
        return []

    entries = _load_kb()
    if not entries:
        return []

    query_lower = complaint.lower()
    query_tokens = _tokenise(query_lower)

    scored = []
    for entry in entries:
        score = _score_entry(entry, query_tokens, species, query_lower)
        if score >= min_score:
            scored.append((score, entry))

    # Sort by score descending, stable (preserves KB order on ties)
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [entry for _, entry in scored[:top_k]]

    logger.debug(
        f"RAG retrieved {len(top)}/{len(entries)} entries for complaint='{complaint[:60]}', "
        f"species='{species}'"
    )
    return top


def format_rag_context(entries: list[dict], species: str = '') -> str:
    """
    Format retrieved KB entries as a concise reference block for the LLM prompt.

    The block is designed to be injected into the triage agent's system prompt
    as supporting clinical reference — not as a diagnosis.
    """
    if not entries:
        return ''

    sp_lower = species.lower().strip() if species else ''
    lines = [
        "=== CLINICAL REFERENCE (from illness knowledge base) ===",
        "Use these evidence-based cues to ground your triage decision. Do NOT name diseases in output.",
        ""
    ]

    for i, e in enumerate(entries, 1):
        lines.append(f"[{i}] {e.get('name', 'Unknown')} (category: {e.get('category', '')})")
        lines.append(f"    Typical urgency: {e.get('typical_urgency', 'Unknown')}")

        escalators = e.get('urgency_escalators', [])
        if escalators:
            lines.append(f"    Escalate to higher tier if: {'; '.join(escalators[:5])}")

        red_flags = e.get('red_flags', [])
        if red_flags:
            lines.append(f"    Red flags in this category: {'; '.join(red_flags)}")

        notes = e.get('key_triage_notes', '')
        if notes:
            lines.append(f"    Triage guidance: {notes}")

        # Species-specific note if available
        sp_notes = e.get('species_notes', {})
        if sp_lower and sp_lower in sp_notes:
            lines.append(f"    Species note ({species}): {sp_notes[sp_lower]}")

        lines.append("")

    lines.append("=== END CLINICAL REFERENCE ===")
    return '\n'.join(lines)
