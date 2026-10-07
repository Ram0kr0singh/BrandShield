"""Evidence-grounded analyst assistance with deterministic fallback."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import Settings
from app.models import AppCandidate, Brand, Detection, DetectionCandidateType, SocialCandidate

logger = logging.getLogger(__name__)


def build_context(detection: Detection, brand: Brand, candidate: AppCandidate | SocialCandidate) -> dict[str, Any]:
    is_app = detection.candidate_type == DetectionCandidateType.APP
    name = candidate.app_name if is_app else (candidate.display_name or candidate.handle)
    url = candidate.store_url if is_app else candidate.profile_url
    source = "App Store" if is_app else "Social Media"
    publisher = candidate.developer_name if is_app else None
    evidence = [
        {
            "signal_type": item.signal_type,
            "available": item.available,
            "score": item.score,
            "details": item.details,
            "priority": item.priority,
        }
        for item in sorted(detection.evidence, key=lambda item: item.priority)
    ]
    return {
        "detection_id": str(detection.id),
        "brand": brand.name,
        "candidate_name": name,
        "source": source,
        "candidate_url": url,
        "candidate_description": candidate.description,
        "publisher_or_developer": publisher,
        "risk_score": detection.risk_score,
        "severity": detection.severity.value,
        "threat_type": detection.threat_type.value if detection.threat_type else None,
        "investigation_status": detection.status.value,
        "official_match": detection.official_match,
        "lookalike_detected": detection.lookalike_detected,
        "detected_at": detection.detected_at.isoformat(),
        "evidence": evidence,
    }


def _label(signal_type: str) -> str:
    return signal_type.replace("_", " ").title()


def deterministic_analysis(context: dict[str, Any]) -> dict[str, Any]:
    """Build conservative prose exclusively from an already normalized context."""
    available = [item for item in context["evidence"] if item["available"]]
    unavailable = [item for item in context["evidence"] if not item["available"]]
    meaningful = [item for item in available if item["signal_type"] != "OFFICIAL_ASSET_MATCH"]
    labels = [_label(item["signal_type"]) for item in meaningful]
    rationale = ", ".join(labels) if labels else "the persisted detection evidence"
    candidate = context["candidate_name"]
    summary = (
        f"{candidate} was flagged by the deterministic engine with an authoritative "
        f"{context['severity']} severity and risk score of {context['risk_score']:.2f}. "
        f"This analyst explanation is based on {rationale}."
    )
    similarity_limited = context["risk_score"] < 50 and not context["official_match"]
    if similarity_limited:
        risk_rationale = "The available evidence indicates name similarity only. Similarity is a review signal and does not by itself establish malicious intent."
    elif context["official_match"]:
        risk_rationale = "An official asset match is recorded. The candidate should be reviewed as a possible legitimate asset or false positive."
    else:
        risk_rationale = f"The deterministic evidence contains {rationale}; a human analyst should assess these signals before making a case decision."
    key_evidence = [
        {"signal_type": item["signal_type"], "summary": _label(item["signal_type"]), "score": item["score"], "details": item["details"]}
        for item in meaningful
    ]
    uncertainties = [f"{_label(item['signal_type'])} is unavailable in the persisted evidence." for item in unavailable]
    uncertainties.append("No external platform confirmation is present in the supplied persisted evidence.")
    actions = ["Review the persisted evidence and candidate metadata."]
    if context["publisher_or_developer"]:
        actions.append("Verify the publisher or developer identity against official brand metadata.")
    if context["candidate_url"]:
        actions.append("Review the persisted candidate URL or platform listing.")
    if context["investigation_status"] == "NEW":
        actions.append("Start an investigation only after human review of the available evidence.")
    else:
        actions.append("Use the existing investigation workflow to record the human decision.")
    if context["source"] == "App Store":
        actions.append("Review an app-store remediation draft only if the analyst confirms a policy concern.")
    return {
        "summary": summary,
        "risk_rationale": risk_rationale,
        "key_evidence": key_evidence,
        "uncertainties": uncertainties,
        "recommended_actions": actions,
        "confidence": "Evidence coverage is based on the persisted signal availability; this is not a replacement risk score.",
        "source_facts": context,
        "generated_at": datetime.now(timezone.utc),
        "provider": "deterministic_fallback",
    }


class AnalystProvider(Protocol):
    def generate(self, context: dict[str, Any]) -> dict[str, Any]: ...


class _AnalystDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1800)
    risk_rationale: str = Field(min_length=1, max_length=1800)
    key_evidence: list[str] = Field(min_length=1, max_length=12)
    uncertainties: list[str] = Field(min_length=1, max_length=12)
    recommended_actions: list[str] = Field(min_length=1, max_length=12)
    confidence: str = Field(min_length=1, max_length=500)


class ProviderFailure(RuntimeError):
    def __init__(
        self,
        category: str,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.status_code = status_code


class GroqAnalystProvider:
    """Server-side Groq Chat Completions adapter; never exposes credentials."""

    def __init__(self, settings: Settings):
        self._settings = settings

    def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        available = {
            item["signal_type"]: item
            for item in context["evidence"]
            if item["available"]
        }
        if not available:
            raise ProviderFailure("evidence_validation", "No available persisted evidence to analyze")

        instructions = (
            "You are BrandShield AI Analyst. Explain only supplied deterministic facts. "
            "Do not create evidence, URLs, publishers, events, scores, severity, or external confirmations. "
            "Do not claim maliciousness from similarity alone. State missing facts as uncertainty. "
            "Return exactly the JSON object required by the response schema; do not echo the input context. "
            "key_evidence must contain only supplied signal_type values whose available field is true."
        )
        schema = _AnalystDraft.model_json_schema()
        schema["properties"]["key_evidence"]["items"]["enum"] = list(available)
        payload = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(context, separators=(",", ":"))},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "brandshield_analyst",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        url = self._settings.llm_base_url.rstrip("/") + "/chat/completions"
        try:
            response = httpx.post(
                url,
                headers={"Authorization": f"Bearer {self._settings.llm_api_key}"},
                json=payload,
                timeout=self._settings.llm_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            body = error.response.text[:2048]
            cloudflare_code = re.search(r"error code:\s*(\d+)", body, re.IGNORECASE)
            if cloudflare_code:
                raise ProviderFailure(
                    "upstream_access_denied",
                    f"Upstream denied the request (Cloudflare error {cloudflare_code.group(1)})",
                    status_code=error.response.status_code,
                ) from error
            status_code = error.response.status_code
            if status_code in (401, 403):
                category = "authentication_or_access"
            elif status_code == 404:
                category = "endpoint_or_model"
            elif status_code == 429:
                category = "rate_limit"
            elif status_code >= 500:
                category = "upstream_server"
            else:
                category = "http_request"
            raise ProviderFailure(
                category,
                f"Provider returned HTTP {status_code}",
                status_code=status_code,
            ) from error
        except httpx.TimeoutException as error:
            category = "timeout"
            raise ProviderFailure(category, f"Provider request failed ({type(error).__name__})") from error
        except httpx.RequestError as error:
            raise ProviderFailure("network_request", f"Provider request failed ({type(error).__name__})") from error
        try:
            body = response.json()
        except (ValueError, UnicodeDecodeError) as error:
            raise ProviderFailure("response_parsing", "Provider response was not valid JSON") from error
        if not isinstance(body, dict):
            raise ProviderFailure("response_parsing", "Provider response had an unexpected shape")
        choices = body.get("choices")
        message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
        output = message.get("content") if isinstance(message, dict) else None
        if not isinstance(output, str):
            raise ProviderFailure("response_parsing", "Provider response did not contain message content")
        try:
            draft = _AnalystDraft.model_validate_json(output)
        except (ValidationError, json.JSONDecodeError) as error:
            raise ProviderFailure("structured_output_validation", "Provider response did not match the analyst schema") from error
        if any(signal not in available for signal in draft.key_evidence):
            raise ProviderFailure("evidence_validation", "Provider response referenced unsupported evidence")
        return {
            "summary": draft.summary,
            "risk_rationale": draft.risk_rationale,
            "key_evidence": [{"signal_type": signal, "summary": _label(signal), "score": available[signal]["score"], "details": available[signal]["details"]} for signal in dict.fromkeys(draft.key_evidence)],
            "uncertainties": draft.uncertainties,
            "recommended_actions": draft.recommended_actions,
            "confidence": draft.confidence,
            "source_facts": context,
            "generated_at": datetime.now(timezone.utc),
            "provider": "groq",
        }


def generate_analysis(context: dict[str, Any], settings: Settings) -> dict[str, Any]:
    """Prefer Groq only when configured; provider issues use deterministic fallback."""
    if not settings.llm_api_key:
        return deterministic_analysis(context)
    try:
        return GroqAnalystProvider(settings).generate(context)
    except ProviderFailure as error:
        logger.warning(
            "Analyst provider fallback provider=groq category=%s exception_type=%s http_status=%s message=%s",
            error.category,
            type(error).__name__,
            error.status_code,
            error,
        )
        return deterministic_analysis(context)
    except Exception as error:
        logger.error(
            "Analyst provider fallback provider=groq category=unexpected_provider_error exception_type=%s",
            type(error).__name__,
        )
        return deterministic_analysis(context)
