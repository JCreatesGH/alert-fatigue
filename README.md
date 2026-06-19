# alert-fatigue

[![CI](https://github.com/JCreatesGH/alert-fatigue/actions/workflows/ci.yml/badge.svg)](https://github.com/JCreatesGH/alert-fatigue/actions)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Turn a wall of pages into a tuning to-do list. `alertfatigue` ingests your alert history and surfaces the noisiest rules, flapping detectors, MTTA, and alerts that **self-resolve without anyone acking them** — then recommends fixes. Works with PagerDuty, Opsgenie, or Alertmanager exports.

![screenshot](assets/screenshot.png)

## Install

```bash
pip install alertfatigue
```

## Use it

```python
from alertfatigue import load_alerts, summary, recommendations

alerts = load_alerts(history)   # [{rule, opened_at, resolved_at?, acked_at?}, ...]

summary(alerts)
# {"total": 3914, "mtta_s": 492, "mttr_s": 1830, "ack_rate": 0.39,
#  "self_resolve_rate": 0.61, "off_hours_rate": 0.44, "flapping_rules": 4, "noisiest": [...]}

for rec in recommendations(alerts):
    print(rec)
# Add a 'for' duration / hysteresis to 'CPUHighWarning' (fired 41× in an hour).
# 'NightlyBackupCheck' pages mostly off-hours (38/40) — route it to a low-urgency queue.
# Demote or auto-close 'PodRestarted' — 460/498 self-resolved without ack.
```

## CLI

Installing the package adds an `alertfatigue` command — feed it a JSON array of alert records:

```bash
$ alertfatigue alerts.json                              # summary + recommendations
$ pd-export | alertfatigue --json                       # machine-readable
$ alertfatigue alerts.json --fail-on-recommendations    # exit 1 to gate CI
```

## What it measures

- **Per-rule noise score** — `rule_report()` ranks rules by signal quality, not raw volume: the score is the count of *unacknowledged* alerts, weighted up when they self-resolve, so a rule that fires often, is rarely acked, and clears on its own rises to the top.
- **Severity inflation** — `severity_breakdown()` shows ack/self-resolve rates per severity, catching the "everything is critical" trap (most `critical` alerts self-resolving → numb to real pages).
- **Noisiest rules** — simple volume ranking.
- **Flapping** — rules that fire ≥ N times within a rolling window (rolling two-pointer, not just per-hour buckets).
- **MTTA / MTTR** — mean time to acknowledge / resolve.
- **Ack rate** — share of alerts a human actually acknowledged (engagement).
- **Self-resolve rate** — share of alerts that resolved quickly and were *never acked*: the textbook definition of noise that paged someone for nothing.
- **Off-hours pages** — `off_hours_report()` measures how many pages fired outside business hours (default 09:00–18:00, Mon–Fri, in the timestamp's own zone) and which rules are the worst offenders — the single biggest on-call-burnout driver.
- **Recommendations** — concrete tuning actions (add hysteresis, demote/auto-close, fix severity inflation, route off-hours noise to a low-urgency queue) per offending rule.

## Development

```bash
pip install -e .[dev] && python -m pytest -q   # 18 tests
```

## License

MIT
