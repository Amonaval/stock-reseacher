from __future__ import annotations

import copy
import json
from datetime import datetime, timezone

PROFILE_VERSION = 1


def ensure_strategy_metadata(strategies: list[dict]) -> list[dict]:
    """Return editable strategy copies while preserving the generated proposal."""
    out = []
    for raw in strategies or []:
        s = copy.deepcopy(raw)
        s.setdefault("enabled", True)
        s.setdefault("generated_name", s.get("name", ""))
        s.setdefault("generated_purpose", s.get("purpose", ""))
        s.setdefault("generated_hard_query", s.get("hard_query", ""))
        s.setdefault("user_notes", "")
        s.setdefault("profile_source", "generated")
        out.append(s)
    return out


def export_strategy_profile(strategies: list[dict], name: str = "My Strategy Philosophy") -> str:
    rows = ensure_strategy_metadata(strategies)
    payload = {
        "profile_version": PROFILE_VERSION,
        "name": name.strip() or "My Strategy Philosophy",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "strategies": rows,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def import_strategy_profile(raw: bytes | str) -> tuple[str, list[dict]]:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("strategies"), list):
        raise ValueError("Invalid strategy profile: expected an object containing a strategies array.")
    version = int(payload.get("profile_version", 0) or 0)
    if version > PROFILE_VERSION:
        raise ValueError(f"Strategy profile version {version} is newer than this app supports ({PROFILE_VERSION}).")
    strategies = ensure_strategy_metadata(payload["strategies"])
    for s in strategies:
        s["profile_source"] = "imported"
    return str(payload.get("name") or "Imported Strategy Philosophy"), strategies


def update_strategy_from_editor(strategy: dict, *, enabled: bool, name: str, purpose: str,
                                hard_query: str, notes: str = "") -> dict:
    s = copy.deepcopy(strategy)
    s["enabled"] = bool(enabled)
    s["name"] = str(name or "").strip()
    s["purpose"] = str(purpose or "").strip()
    s["hard_query"] = str(hard_query or "").strip()
    s["user_notes"] = str(notes or "").strip()
    s["profile_source"] = "user_tuned"
    return s
