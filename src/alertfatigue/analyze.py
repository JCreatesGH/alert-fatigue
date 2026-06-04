"""Noise / flapping / MTTA analysis."""
from __future__ import annotations
from collections import Counter, defaultdict
from typing import Dict, List
from .model import Alert


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


def self_resolve_rate(alerts: List[Alert], quick_s: float = 300) -> float:
    """Fraction of alerts that resolved quickly and were never acked — i.e. noise
    that paged someone for nothing."""
    if not alerts:
        return 0.0
    noise = sum(1 for a in alerts
                if not a.was_acked and a.duration_s is not None and a.duration_s <= quick_s)
    return round(noise / len(alerts), 3)


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
    return recs


def summary(alerts: List[Alert]) -> Dict[str, object]:
    return {
        "total": len(alerts),
        "unique_rules": len({a.rule for a in alerts}),
        "mtta_s": mtta(alerts),
        "self_resolve_rate": self_resolve_rate(alerts),
        "flapping_rules": len(flapping_rules(alerts)),
        "noisiest": noisiest(alerts, 5),
    }
