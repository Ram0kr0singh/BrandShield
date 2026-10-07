from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from app.detection.normalization import analyze_name, normalize_text
from app.models import AppCandidate, Brand, OfficialApp, OfficialSocialAccount, SocialCandidate


@dataclass(frozen=True)
class Signal:
    signal_type: str
    available: bool
    score: float | None
    priority: int
    details: dict


def name_signal(brand: Brand, candidate_name: str) -> tuple[Signal, dict]:
    analysis = analyze_name(brand.name, candidate_name)
    return Signal("NAME_SIMILARITY", True, analysis.similarity, 2, analysis.as_dict()), analysis.as_dict()


def lookalike_signal(name_result: dict) -> Signal:
    return Signal(
        "LOOKALIKE_NAME",
        True,
        100.0 if name_result["detected"] else 0.0,
        3,
        {
            "detected": name_result["detected"],
            "official_name": name_result.get("official_name"),
            "candidate_name": name_result.get("candidate_name"),
            "transformations": name_result["transformations"],
        },
    )


def description_signal(candidate_description: str | None, official_descriptions: list[str]) -> Signal:
    references = [item for item in official_descriptions if item]
    if not candidate_description or not references:
        return Signal("DESCRIPTION_SIMILARITY", False, None, 5, {"reason": "No comparable official and candidate descriptions are available."})
    candidate = normalize_text(candidate_description)
    scores = []
    for reference in references:
        official = normalize_text(reference)
        sequence = SequenceMatcher(None, official, candidate).ratio() * 100
        official_tokens, candidate_tokens = set(official.split()), set(candidate.split())
        overlap = (len(official_tokens & candidate_tokens) / len(official_tokens | candidate_tokens) * 100) if official_tokens or candidate_tokens else 0
        scores.append(max(sequence, overlap))
    return Signal("DESCRIPTION_SIMILARITY", True, round(max(scores), 2), 5, {"candidate_description": candidate_description, "official_reference_count": len(references)})


def social_official_signal(candidate: SocialCandidate, official_accounts: list[OfficialSocialAccount]) -> Signal:
    match = next((item for item in official_accounts if item.platform == candidate.platform and (item.handle.lower() == candidate.handle.lower() or item.profile_url == candidate.profile_url)), None)
    return Signal("OFFICIAL_ASSET_MATCH", True, None, 1, {"matched": match is not None, "matched_by": "platform_and_handle_or_profile_url" if match else None, "official_account_id": str(match.id) if match else None})


def app_official_signal(candidate: AppCandidate, official_apps: list[OfficialApp]) -> Signal:
    match = next((item for item in official_apps if item.platform == candidate.platform and (item.package_identifier == candidate.package_identifier or item.store_url == candidate.store_url)), None)
    return Signal("OFFICIAL_ASSET_MATCH", True, None, 1, {"matched": match is not None, "matched_by": "platform_and_package_or_store_url" if match else None, "official_app_id": str(match.id) if match else None})


def publisher_signal(candidate: AppCandidate, official_apps: list[OfficialApp]) -> Signal:
    if not candidate.developer_name or not official_apps:
        return Signal("PUBLISHER_MISMATCH", False, None, 4, {"result": "UNKNOWN"})
    match = next((item for item in official_apps if normalize_text(item.developer_name) == normalize_text(candidate.developer_name) or (candidate.developer_identifier and item.developer_identifier == candidate.developer_identifier)), None)
    return Signal("PUBLISHER_MISMATCH", True, 0.0 if match else 100.0, 4, {"result": "MATCH" if match else "MISMATCH", "candidate_developer": candidate.developer_name, "official_developers": [item.developer_name for item in official_apps]})


def logo_signal() -> Signal:
    return Signal("LOGO_SIMILARITY", False, None, 6, {"reason": "Only remote synthetic URL references are present; no comparable local image data exists."})
