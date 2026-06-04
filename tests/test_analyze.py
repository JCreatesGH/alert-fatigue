from datetime import datetime, timedelta, timezone
from alertfatigue import (load_alerts, noisiest, flapping_rules, mtta,
                          self_resolve_rate, recommendations, summary)

BASE = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)


def at(mins):
    return BASE + timedelta(minutes=mins)


def make(rule, open_min, resolved_min=None, acked_min=None):
    return {"rule": rule, "opened_at": at(open_min).isoformat(),
            "resolved_at": at(resolved_min).isoformat() if resolved_min is not None else None,
            "acked_at": at(acked_min).isoformat() if acked_min is not None else None}


def test_noisiest():
    alerts = load_alerts([make("CPUHigh", i) for i in range(8)] + [make("DiskFull", 0)])
    top = noisiest(alerts)
    assert top[0] == ("CPUHigh", 8)


def test_flapping_detection():
    # CPUHigh fires 6 times within 30 minutes -> flapping
    alerts = load_alerts([make("CPUHigh", i * 5) for i in range(6)] + [make("Calm", 0)])
    flap = flapping_rules(alerts, window_s=3600, min_count=5)
    assert "CPUHigh" in flap and flap["CPUHigh"] >= 5
    assert "Calm" not in flap


def test_mtta():
    alerts = load_alerts([make("A", 0, acked_min=2), make("A", 10, acked_min=14)])
    assert mtta(alerts) == 180.0   # (120 + 240) / 2


def test_self_resolve_rate():
    alerts = load_alerts([
        make("Noise", 0, resolved_min=2),       # quick, unacked -> noise
        make("Noise", 10, resolved_min=12),      # noise
        make("Real", 20, resolved_min=60, acked_min=22),  # acked, not noise
    ])
    assert self_resolve_rate(alerts) == round(2/3, 3)


def test_recommendations():
    alerts = load_alerts([make("CPUHigh", i * 5, resolved_min=i*5 + 1) for i in range(6)])
    recs = recommendations(alerts)
    assert any("hysteresis" in r or "auto-close" in r for r in recs)


def test_summary():
    alerts = load_alerts([make("A", 0, acked_min=1), make("B", 5)])
    s = summary(alerts)
    assert s["total"] == 2 and s["unique_rules"] == 2
