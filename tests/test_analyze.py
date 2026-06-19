from datetime import datetime, timedelta, timezone
from alertfatigue import (load_alerts, noisiest, flapping_rules, mtta, mttr,
                          ack_rate, self_resolve_rate, rule_report, severity_breakdown,
                          off_hours_report, recommendations, summary)

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
    assert "mttr_s" in s and "ack_rate" in s


def test_mttr_and_ack_rate():
    alerts = load_alerts([
        make("A", 0, resolved_min=2, acked_min=1),   # 120s to resolve, acked
        make("B", 10, resolved_min=14),               # 240s to resolve, not acked
    ])
    assert mttr(alerts) == 180.0          # (120 + 240) / 2
    assert ack_rate(alerts) == 0.5        # 1 of 2 acked


def test_load_alerts_skips_records_without_open_time():
    alerts = load_alerts([
        {"rule": "A", "opened_at": at(0).isoformat()},
        {"rule": "B"},                                 # no opened_at / ts -> skipped
    ])
    assert [a.rule for a in alerts] == ["A"]


def test_rule_report_ranks_noisy_low_signal_rules_first():
    alerts = load_alerts(
        [make("Noise", i, resolved_min=i + 1) for i in range(10)]                  # 10× unacked, quick self-resolve
        + [make("Real", i * 5, resolved_min=i * 5 + 30, acked_min=i * 5 + 1) for i in range(3)]  # acked, real
    )
    report = rule_report(alerts)
    assert report[0].rule == "Noise"
    noise = next(r for r in report if r.rule == "Noise")
    real = next(r for r in report if r.rule == "Real")
    assert noise.noise_score > real.noise_score
    assert noise.ack_rate == 0.0 and noise.self_resolve_rate == 1.0
    assert real.ack_rate == 1.0 and real.noise_score == 0.0


def _sev(rule, mins, severity, resolved=True):
    r = {"rule": rule, "opened_at": at(mins).isoformat(), "severity": severity}
    if resolved:
        r["resolved_at"] = at(mins).isoformat()   # instant, unacked -> self-resolved noise
    return r


def test_severity_breakdown_and_inflation_recommendation():
    alerts = load_alerts([_sev("X", i, "critical") for i in range(4)])
    sb = severity_breakdown(alerts)
    assert sb["critical"]["count"] == 4
    assert sb["critical"]["self_resolve_rate"] == 1.0
    assert any("inflation" in r.lower() for r in recommendations(alerts))


def test_summary_includes_severity_and_top_noise():
    alerts = load_alerts([make("A", 0, acked_min=1), make("B", 5)])
    s = summary(alerts)
    assert "by_severity" in s and "top_noise" in s
    assert "off_hours_rate" in s


def test_off_hours_report():
    # 2026-06-01 is a Monday; 2026-06-06 is a Saturday
    alerts = load_alerts([
        {"rule": "A", "opened_at": "2026-06-01T03:00:00Z"},   # Mon 03:00 -> off (too early)
        {"rule": "A", "opened_at": "2026-06-01T14:00:00Z"},   # Mon 14:00 -> business hours
        {"rule": "A", "opened_at": "2026-06-01T20:00:00Z"},   # Mon 20:00 -> off (too late)
        {"rule": "B", "opened_at": "2026-06-06T14:00:00Z"},   # Sat 14:00 -> off (weekend)
    ])
    rep = off_hours_report(alerts)
    assert rep["total"] == 4
    assert rep["off_hours"] == 3 and rep["off_hours_rate"] == 0.75
    by_rule = dict(rep["by_rule"])
    assert by_rule["A"] == 2 and by_rule["B"] == 1


def test_off_hours_recommendation():
    # a rule that fires only off-hours (nights) -> should be recommended for re-routing
    recs = recommendations(load_alerts([
        {"rule": "NightlyBackupNoise", "opened_at": f"2026-06-0{d}T02:00:00Z"} for d in (1, 2, 3, 4)
    ]))
    assert any("off-hours" in r for r in recs)


def test_off_hours_respects_business_window():
    alerts = load_alerts([{"rule": "A", "opened_at": "2026-06-01T08:00:00Z"}])  # Mon 08:00
    assert off_hours_report(alerts)["off_hours"] == 1                       # before default 9:00
    assert off_hours_report(alerts, business_start=7)["off_hours"] == 0     # widen window -> in-hours
