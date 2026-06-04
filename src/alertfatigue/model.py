"""Alert event model."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Alert:
    rule: str
    opened_at: datetime
    resolved_at: Optional[datetime] = None
    acked_at: Optional[datetime] = None
    severity: str = "warning"

    @property
    def duration_s(self) -> Optional[float]:
        if self.resolved_at:
            return (self.resolved_at - self.opened_at).total_seconds()
        return None

    @property
    def ack_latency_s(self) -> Optional[float]:
        if self.acked_at:
            return (self.acked_at - self.opened_at).total_seconds()
        return None

    @property
    def was_acked(self) -> bool:
        return self.acked_at is not None


def _dt(v: Any) -> Optional[datetime]:
    if not v:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def load_alerts(records: List[Dict[str, Any]]) -> List[Alert]:
    out = []
    for r in records:
        out.append(Alert(
            rule=r.get("rule", r.get("name", "unknown")),
            opened_at=_dt(r.get("opened_at") or r.get("ts")),
            resolved_at=_dt(r.get("resolved_at")),
            acked_at=_dt(r.get("acked_at")),
            severity=r.get("severity", "warning"),
        ))
    return out
