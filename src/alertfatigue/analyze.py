"""Noise / flapping / MTTA analysis."""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional
from .model import Alert

# Severities that should mean "wake someone up" — self-resolving ones here = inflation.
_HIGH_SEVERITIES = {"critical", "page", "high", "p1", "sev1"}


def noisiest(alerts: List[Alert], top: int = 10) -> List[tuple]:
    c = Counter(a.rule for a in alerts)
    return c.most_common(top)


def flapping_rules(alerts: List[Alert], window_s: float = 3600, min_count: int = 5) -> Dict[str, int]:
    """Rules that fire >= min_count times within any rolling window_s."""
    by_rule: Dict[str, List[float]] = defaultdict(list)
    for a in alerts:
        by_rule[a.rule].append(a.opened_at.timestamp())
    out: Dict[str, int] = {}
    for rule, times in by_rule.items():
        times.sort()
        best = 0
        j = 0
        for i in range(len(times)):
            while times[i] - times[j] > window_s:
                j += 1
            best = max(best, i - j + 1)
        if best >= min_count:
            out[rule] = best
    return out


def mtta(alerts: List[Alert]) -> float:
    """Mean time to acknowledge, in seconds (only acked alerts)."""
    lats = [a.ack_latency_s for a in alerts if a.ack_latency_s is not None]
    return round(sum(lats) / len(lats), 1) if lats else 0.0


def mttr(alerts: List[Alert]) -> float:
    """Mean time to resolve, in seconds (only resolved alerts)."""
    durs = [a.duration_s for a in alerts if a.duration_s is not None]
    return round(sum(durs) / len(durs), 1) if durs else 0.0


def ack_rate(alerts: List[Alert]) -> float:
    """Fraction of alerts a human acknowledged (engagement / signal)."""
    if not alerts:
        return 0.0
    return round(sum(1 for a in alerts if a.was_acked) / len(alerts), 3)


def self_resolve_rate(alerts: List[Alert], quick_s: float = 300) -> float:
    """Fraction of alerts that resolved quickly and were never acked — i.e. noise
    that paged someone for nothing."""
    if not alerts:
        return 0.0
    noise = sum(1 for a in alerts
                if not a.was_acked and a.duration_s is not None and a.duration_s <= quick_s)
    return round(noise / len(alerts), 3)


@dataclass
class RuleStats:
    rule: str
    count: int
    ack_rate: float
    self_resolve_rate: float
    mttr_s: float
    noise_score: float        # higher = noisier / lower-signal


def rule_report(alerts: List[Alert], top: Optional[int] = None) -> List[RuleStats]:
    """Per-rule signal-quality report, worst (noisiest) first. The noise score is
    the volume of *unacknowledged* alerts, weighted up when they self-resolve — so
    a rule that fires often, is rarely acked, and clears on its own ranks highest."""
    by_rule: Dict[str, List[Alert]] = defaultdict(list)
    for a in alerts:
        by_rule[a.rule].append(a)
    out: List[RuleStats] = []
    for rule, group in by_rule.items():
        ar = ack_rate(group)
        sr = self_resolve_rate(group)
        score = round(len(group) * (1 - ar) * (0.5 + 0.5 * sr), 2)
        out.append(RuleStats(rule, len(group), ar, sr, mttr(group), score))
    out.sort(key=lambda r: (-r.noise_score, -r.count, r.rule))
    return out[:top] if top is not None else out


def severity_breakdown(alerts: List[Alert]) -> Dict[str, Dict[str, float]]:
    """Per-severity counts plus ack/self-resolve rates — surfaces severity
    inflation (e.g. 'critical' alerts that mostly self-resolve)."""
    by_sev: Dict[str, List[Alert]] = defaultdict(list)
    for a in alerts:
        by_sev[a.severity].append(a)
    return {sev: {"count": len(g), "ack_rate": ack_rate(g),
                  "self_resolve_rate": self_resolve_rate(g)}
            for sev, g in by_sev.items()}


def recommendations(alerts: List[Alert]) -> List[str]:
    recs: List[str] = []
    flap = flapping_rules(alerts)
    for rule, n in sorted(flap.items(), key=lambda x: -x[1]):
        recs.append(f"Add a 'for' duration / hysteresis to '{rule}' (fired {n}× in an hour).")
    # rules that mostly self-resolve
    by_rule_total: dict = {}
    by_rule_noise: dict = {}
    for a in alerts:
        by_rule_total[a.rule] = by_rule_total.get(a.rule, 0) + 1
        if not a.was_acked and a.duration_s is not None and a.duration_s <= 300:
            by_rule_noise[a.rule] = by_rule_noise.get(a.rule, 0) + 1
    for rule, total in by_rule_total.items():
        noise = by_rule_noise.get(rule, 0)
        if total >= 3 and noise / total >= 0.7:
            recs.append(f"Demote or auto-close '{rule}' — {noise}/{total} self-resolved without ack.")
    # severity inflation: a high severity whose alerts mostly self-resolve isn't critical
    for sev, stats in severity_breakdown(alerts).items():
        if sev.lower() in _HIGH_SEVERITIES and stats["count"] >= 3 and stats["self_resolve_rate"] >= 0.5:
            recs.append(
                f"Severity inflation: {stats['self_resolve_rate']*100:.0f}% of '{sev}' alerts "
                f"self-resolved without ack — downgrade the severity so real pages stand out.")
    return recs


def summary(alerts: List[Alert]) -> Dict[str, object]:
    return {
        "total": len(alerts),
        "unique_rules": len({a.rule for a in alerts}),
        "mtta_s": mtta(alerts),
        "mttr_s": mttr(alerts),
        "ack_rate": ack_rate(alerts),
        "self_resolve_rate": self_resolve_rate(alerts),
        "flapping_rules": len(flapping_rules(alerts)),
        "noisiest": noisiest(alerts, 5),
        "by_severity": severity_breakdown(alerts),
        "top_noise": [(r.rule, r.noise_score) for r in rule_report(alerts, top=5)],
    }
