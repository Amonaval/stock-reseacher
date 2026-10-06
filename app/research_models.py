from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ResearchEvent:
    at: str
    stage: str
    action: str
    message: str
    company: str = ""
    status: str = "INFO"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchDecision:
    stage: str
    decision: str
    reason: str
    at: str = field(default_factory=utc_now)
    evidence_coverage: float | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompanyResearch:
    company: str
    screener_url: str = ""
    nse_symbol: str = ""
    bse_code: str = ""
    screen_matches: list[str] = field(default_factory=list)
    screen_snapshots: list[dict[str, Any]] = field(default_factory=list)
    financial_history: list[dict[str, Any]] = field(default_factory=list)
    financial_assessment: dict[str, Any] = field(default_factory=dict)
    documents: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    research_questions: list[dict[str, Any]] = field(default_factory=list)
    bull_case: dict[str, Any] = field(default_factory=dict)
    bear_case: dict[str, Any] = field(default_factory=dict)
    contradiction_review: dict[str, Any] = field(default_factory=dict)
    decisions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ResearchRun:
    run_id: str
    created_at: str
    status: str = "CREATED"
    research_depth: str = "Deep"
    capital: float = 100000.0
    selected_screens: list[dict[str, Any]] = field(default_factory=list)
    strategies: list[dict[str, Any]] = field(default_factory=list)
    companies: dict[str, CompanyResearch] = field(default_factory=dict)
    events: list[ResearchEvent] = field(default_factory=list)
    stage_summary: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, research_depth: str = "Deep", capital: float = 100000.0) -> "ResearchRun":
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return cls(run_id=f"run-{stamp}-{uuid.uuid4().hex[:6]}", created_at=utc_now(), research_depth=research_depth, capital=float(capital))

    def log(self, stage: str, action: str, message: str, *, company: str = "", status: str = "INFO", details: dict[str, Any] | None = None) -> None:
        self.events.append(ResearchEvent(utc_now(), stage, action, message, company, status, details or {}))

    def ensure_company(self, company: str, screener_url: str = "") -> CompanyResearch:
        key = " ".join(str(company or "").split()).casefold()
        if key not in self.companies:
            self.companies[key] = CompanyResearch(company=" ".join(str(company or "").split()), screener_url=screener_url)
        elif screener_url and not self.companies[key].screener_url:
            self.companies[key].screener_url = screener_url
        return self.companies[key]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchRun":
        obj = cls(
            run_id=data["run_id"], created_at=data.get("created_at", utc_now()), status=data.get("status", "CREATED"),
            research_depth=data.get("research_depth", "Deep"), capital=float(data.get("capital", 100000)),
            selected_screens=data.get("selected_screens", []), strategies=data.get("strategies", []), stage_summary=data.get("stage_summary", {}),
        )
        obj.events = [ResearchEvent(**x) for x in data.get("events", [])]
        obj.companies = {k: CompanyResearch(**v) for k, v in data.get("companies", {}).items()}
        return obj

    def save(self, root: Path) -> Path:
        folder = Path(root) / self.run_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "research_run.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path
