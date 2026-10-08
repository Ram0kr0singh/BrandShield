from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher


CONFUSABLES = {"1": "i", "l": "i", "!": "i", "|": "l", "0": "o", "3": "e", "4": "a", "5": "s", "@": "a", "$": "s"}
MULTI_CHARACTER_CONFUSABLES = {"rn": "m", "vv": "w", "cl": "d"}
HOMOGLYPHS = {"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "А": "A", "Е": "E", "О": "O", "Р": "P", "С": "C", "Х": "X", "У": "Y", "І": "I"}


def _replace_homoglyphs(value: str) -> tuple[str, list[dict]]:
    replacements, mapped = [], []
    for position, character in enumerate(value):
        replacement = HOMOGLYPHS.get(character, character)
        mapped.append(replacement)
        if replacement != character:
            replacements.append({"type": "HOMOGLYPH_SUBSTITUTION", "position": position, "from": character, "to": replacement.lower(), "code_points": [f"U+{ord(character):04X}"]})
    return "".join(mapped), replacements


def _normalized(value: str, replace_homoglyphs: bool = True) -> str:
    if replace_homoglyphs:
        value, _ = _replace_homoglyphs(value)
    value = unicodedata.normalize("NFKC", value).lower()
    return " ".join(re.sub(r"[^\w\s]", " ", value).split())


def normalize_text(value: str) -> str:
    """Normalize comparison text without modifying its stored source value."""
    return _normalized(value)


def _canonical_character(character: str) -> str:
    seen: set[str] = set()
    while character in CONFUSABLES and character not in seen:
        seen.add(character)
        character = CONFUSABLES[character]
    return character


def _canonical_units(value: str) -> list[tuple[str, str]]:
    mapped, _ = _replace_homoglyphs(value)
    comparable = unicodedata.normalize("NFKC", mapped).lower()
    units, index = [], 0
    while index < len(comparable):
        pair = comparable[index:index + 2]
        if pair in MULTI_CHARACTER_CONFUSABLES:
            units.append((MULTI_CHARACTER_CONFUSABLES[pair], pair))
            index += 2
            continue
        character = comparable[index]
        canonical = _canonical_character(character)
        if canonical.isalnum():
            units.append((canonical, character))
        index += 1
    return units


def _canonical(value: str) -> str:
    return "".join(character for character, _ in _canonical_units(value))


def _damerau_levenshtein(left: str, right: str) -> int:
    previous_previous: list[int] | None = None
    previous = list(range(len(right) + 1))
    for row, left_character in enumerate(left, start=1):
        current = [row]
        for column, right_character in enumerate(right, start=1):
            cost = int(left_character != right_character)
            value = min(previous[column] + 1, current[column - 1] + 1, previous[column - 1] + cost)
            if previous_previous is not None and row > 1 and column > 1 and left_character == right[column - 2] and left[row - 2] == right_character:
                value = min(value, previous_previous[column - 2] + 1)
            current.append(value)
        previous_previous, previous = previous, current
    return previous[-1]


def _substitutions(official: str, candidate: str) -> list[dict]:
    official_units, candidate_units = _canonical_units(official), _canonical_units(candidate)
    if "".join(unit[0] for unit in official_units) != "".join(unit[0] for unit in candidate_units):
        return []
    return [{"type": "CHARACTER_SUBSTITUTION", "position": position, "from": official_character, "to": candidate_chunk} for position, ((official_character, _), (_, candidate_chunk)) in enumerate(zip(official_units, candidate_units)) if official_character != candidate_chunk]


def _edit_transformation(official: str, candidate: str) -> dict | None:
    limit = 2 if len(official) >= 8 else 1
    if len(official) < 4 or _damerau_levenshtein(official, candidate) > limit:
        return None
    if len(official) == len(candidate):
        differences = [index for index, (left, right) in enumerate(zip(official, candidate)) if left != right]
        if len(differences) == 2 and differences[1] == differences[0] + 1:
            index = differences[0]
            if official[index] == candidate[index + 1] and official[index + 1] == candidate[index]:
                return {"type": "CHARACTER_TRANSPOSITION", "position": index, "from": official[index:index + 2], "to": candidate[index:index + 2]}
        return None
    if len(candidate) == len(official) + 1:
        matches = [index for index in range(len(candidate)) if candidate[:index] + candidate[index + 1:] == official]
        if matches:
            # Equivalent removals exist in doubled suffixes (Nikee). Prefer
            # the terminal insertion over labelling it a repeated character.
            index = next((item for item in matches if item in {0, len(candidate) - 1}), matches[0])
            kind = "REPEATED_CHARS" if 0 < index < len(candidate) - 1 and ((candidate[index] == candidate[index - 1]) or (candidate[index] == candidate[index + 1])) else "CHARACTER_INSERTION"
            return {"type": kind, "position": index, "character": candidate[index]}
    if len(official) == len(candidate) + 1:
        for index in range(len(official)):
            if official[:index] + official[index + 1:] == candidate:
                return {"type": "CHARACTER_OMISSION", "position": index, "character": official[index]}
    return None


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
    official, candidate = normalize_text(official_name), normalize_text(candidate_name)
    raw_official, raw_candidate = _normalized(official_name, False), _normalized(candidate_name, False)
    condensed_official, condensed_candidate = "".join(official.split()), "".join(candidate.split())
    canonical_official, canonical_candidate = _canonical(official_name), _canonical(candidate_name)
    direct = SequenceMatcher(None, condensed_official, condensed_candidate).ratio() * 100
    canonical = SequenceMatcher(None, canonical_official, canonical_candidate).ratio() * 100
    candidate_tokens = candidate.split()
    canonical_candidate_tokens = [_canonical(token) for token in candidate_tokens]
    token_similarity = max((SequenceMatcher(None, canonical_official, token).ratio() * 100 for token in canonical_candidate_tokens), default=0.0)
    # Exact official handles/names go through official matching, never this signal.
    if raw_official == raw_candidate:
        return NameAnalysis(official_name, candidate_name, official, candidate, round(max(direct, canonical, token_similarity), 2), False, [])

    _, transformations = _replace_homoglyphs(candidate_name)
    official_tokens, canonical_official_tokens = official.split(), [_canonical(token) for token in official.split()]
    bases: list[str] = []
    if canonical_candidate == canonical_official:
        transformations.extend(_substitutions(official_name, candidate_name))
        bases.append(candidate_name)
    if official_tokens and canonical_candidate_tokens[:len(official_tokens)] == canonical_official_tokens and len(candidate_tokens) > len(official_tokens):
        transformations.append({"type": "ADDED_WORDS", "tokens": candidate_tokens[len(official_tokens):]})
        bases.append(candidate_tokens[0])
    elif official_tokens and canonical_candidate_tokens[-len(official_tokens):] == canonical_official_tokens and len(candidate_tokens) > len(official_tokens):
        transformations.append({"type": "ADDED_WORDS", "tokens": candidate_tokens[:-len(official_tokens)]})
        bases.append(candidate_tokens[-1])
    if condensed_official == condensed_candidate and official != candidate:
        transformations.append({"type": "SPACING_VARIATION"})
    for base in bases + candidate_tokens or [canonical_candidate]:
        edit = _edit_transformation(canonical_official, _canonical(base))
        if edit is not None:
            transformations.append(edit)
            break
    return NameAnalysis(official_name, candidate_name, official, candidate, round(max(direct, canonical, token_similarity), 2), bool(transformations), transformations)
