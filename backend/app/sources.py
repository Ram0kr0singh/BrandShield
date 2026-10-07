"""In-memory source availability registry for honest demo status and outage simulation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Literal

from fastapi import APIRouter, HTTPException

SourceKind = Literal["SOCIAL", "APP", "DEMO"]
SourceStatus = Literal["ONLINE", "DEGRADED", "NOT_CONFIGURED"]
NOT_CONFIGURED_MESSAGE = "Live collection is not enabled in this prototype. Using stored observations."
SIMULATED_OUTAGE_MESSAGE = "Source unreachable (simulated for demo). Showing last stored data."

router = APIRouter(prefix="/sources", tags=["sources"])
_lock = RLock()

_DEFAULTS: tuple[dict, ...] = (
    {
        "id": "demo_dataset",
        "name": "Controlled demo dataset",
        "kind": "DEMO",
        "status": "ONLINE",
        "message": "Stored controlled observations are available.",
        "last_checked_at": None,
        "last_success_at": None,
        "simulated": False,
    },
    {
        "id": "instagram",
        "name": "Instagram live monitor",
        "kind": "SOCIAL",
        "status": "NOT_CONFIGURED",
        "message": NOT_CONFIGURED_MESSAGE,
        "last_checked_at": None,
        "last_success_at": None,
        "simulated": False,
    },
    {
        "id": "google_play",
        "name": "Google Play live monitor",
        "kind": "APP",
        "status": "NOT_CONFIGURED",
        "message": NOT_CONFIGURED_MESSAGE,
        "last_checked_at": None,
        "last_success_at": None,
        "simulated": False,
    },
    {
        "id": "app_store",
        "name": "Apple App Store live monitor",
        "kind": "APP",
        "status": "NOT_CONFIGURED",
        "message": NOT_CONFIGURED_MESSAGE,
        "last_checked_at": None,
        "last_success_at": None,
        "simulated": False,
    },
)
_sources: dict[str, dict] = {source["id"]: deepcopy(source) for source in _DEFAULTS}
_live_source_ids = frozenset({"instagram", "google_play", "app_store"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def reset_source_status() -> None:
    """Reset the process-local registry; intended for deterministic tests."""
    with _lock:
        _sources.clear()
        _sources.update({source["id"]: deepcopy(source) for source in _DEFAULTS})


def _get_source_or_404(source_id: str) -> dict:
    source = _sources.get(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


def _touch(source: dict) -> None:
    checked_at = _now()
    source["last_checked_at"] = checked_at
    if source["status"] == "ONLINE":
        source["last_success_at"] = checked_at


def source_status() -> list[dict]:
    """Return ordered source status snapshots, updating only in-memory check times."""
    with _lock:
        for source in _sources.values():
            _touch(source)
        return [deepcopy(source) for source in _sources.values()]


def degraded_source_warnings() -> list[dict[str, str]]:
    """Return scan warnings for sources currently marked degraded."""
    with _lock:
        warnings = []
        for source in _sources.values():
            _touch(source)
            if source["status"] == "DEGRADED":
                warnings.append({
                    "id": source["id"],
                    "name": source["name"],
                    "status": source["status"],
                    "message": source["message"],
                })
        return warnings


def _simulate_outage(source_id: str) -> dict:
    with _lock:
        source = _get_source_or_404(source_id)
        if source_id not in _live_source_ids:
            raise HTTPException(status_code=409, detail="The controlled demo dataset cannot be taken offline")
        source.update({
            "status": "DEGRADED",
            "message": SIMULATED_OUTAGE_MESSAGE,
            "last_checked_at": _now(),
            "simulated": True,
        })
        return {**deepcopy(source), "simulated": True}


def _restore_source(source_id: str) -> dict:
    with _lock:
        source = _get_source_or_404(source_id)
        if source_id not in _live_source_ids:
            raise HTTPException(status_code=409, detail="The controlled demo dataset cannot be taken offline")
        source.update({
            "status": "NOT_CONFIGURED",
            "message": NOT_CONFIGURED_MESSAGE,
            "last_checked_at": _now(),
            "simulated": False,
        })
        return {**deepcopy(source), "simulated": True}


@router.get("/status")
def get_source_status() -> list[dict]:
    return source_status()


@router.post("/{source_id}/simulate-outage")
def simulate_source_outage(source_id: str) -> dict:
    """DEMO ONLY: mark an unconfigured live source as unavailable in memory."""
    return _simulate_outage(source_id)


@router.post("/{source_id}/restore")
def restore_source(source_id: str) -> dict:
    """DEMO ONLY: clear the simulated outage; no live connection is made."""
    return _restore_source(source_id)
