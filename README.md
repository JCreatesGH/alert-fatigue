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
# {"total": 3914, "mtta_s": 492, "self_resolve_rate": 0.61, "flapping_rules": 4, "noisiest": [...]}

for rec in recommendations(alerts):
    print(rec)
# Add a 'for' duration / hysteresis to 'CPUHighWarning' (fired 41× in an hour).
# Demote or auto-close 'PodRestarted' — 460/498 self-resolved without ack.
```

## What it measures

- **Noisiest rules** — simple volume ranking.
- **Flapping** — rules that fire ≥ N times within a rolling window (rolling two-pointer, not just per-hour buckets).
- **MTTA** — mean time to acknowledge across acked alerts.
- **Self-resolve rate** — share of alerts that resolved quickly and were *never acked*: the textbook definition of noise that paged someone for nothing.
- **Recommendations** — concrete tuning actions (add hysteresis, demote/auto-close) per offending rule.

## Development

```bash
python -m pytest -q   # 6 tests
```

## License

MIT
