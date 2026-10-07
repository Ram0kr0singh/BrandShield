from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher


CONFUSABLES = {"1": "i", "0": "o", "3": "e", "4": "a", "5": "s"}


def normalize_text(value: str) -> str:
    """Normalize comparison text without modifying its stored source value."""
    value = unicodedata.normalize("NFKC", value).lower()
    return " ".join(re.sub(r"[^\w\s]", " ", value).split())


def _canonical(value: str) -> str:
    return "".join(CONFUSABLES.get(char, char) for char in normalize_text(value) if char.isalnum())


@dataclass(frozen=True)
class NameAnalysis:
    official_name: str
    candidate_name: str
    normalized_official: str
    normalized_candidate: str
    similarity: float
    detected: bool
    transformations: list[dict]

    def as_dict(self) -> dict:
        return asdict(self)


def analyze_name(official_name: str, candidate_name: str) -> NameAnalysis:
    official = normalize_text(official_name)
    candidate = normalize_text(candidate_name)
    condensed_official = "".join(official.split())
    condensed_candidate = "".join(candidate.split())
    direct = SequenceMatcher(None, condensed_official, condensed_candidate).ratio() * 100
    canonical_official = _canonical(official_name)
    canonical = SequenceMatcher(None, canonical_official, _canonical(candidate_name)).ratio() * 100
    token_similarity = max((SequenceMatcher(None, canonical_official, _canonical(token)).ratio() * 100 for token in candidate.split()), default=0.0)
    transformations: list[dict] = []
    comparable_candidate = condensed_candidate[: len(condensed_official)]
    if len(condensed_official) == len(comparable_candidate) and _canonical(comparable_candidate) == canonical_official:
        for position, (source, replacement) in enumerate(zip(condensed_official, comparable_candidate)):
            if source != replacement and CONFUSABLES.get(replacement) == source:
                transformations.append({"type": "CHARACTER_SUBSTITUTION", "position": position, "from": source, "to": replacement})
    official_tokens = official.split()
    candidate_tokens = candidate.split()
    canonical_official_tokens = [_canonical(token) for token in official_tokens]
    canonical_candidate_tokens = [_canonical(token) for token in candidate_tokens]
    if official_tokens and canonical_candidate_tokens[: len(official_tokens)] == canonical_official_tokens and len(candidate_tokens) > len(official_tokens):
        transformations.append({"type": "ADDED_WORDS", "tokens": candidate_tokens[len(official_tokens) :]})
    elif official_tokens and canonical_candidate_tokens[-len(official_tokens) :] == canonical_official_tokens and len(candidate_tokens) > len(official_tokens):
        transformations.append({"type": "ADDED_WORDS", "tokens": candidate_tokens[: -len(official_tokens)]})
    if condensed_official == condensed_candidate and official != candidate:
        transformations.append({"type": "SPACING_VARIATION"})
    return NameAnalysis(official_name, candidate_name, official, candidate, round(max(direct, canonical, token_similarity), 2), bool(transformations), transformations)
