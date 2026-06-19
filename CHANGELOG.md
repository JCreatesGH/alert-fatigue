# Changelog

All notable changes are documented here, following
[Keep a Changelog](https://keepachangelog.com/) and [SemVer](https://semver.org/).

## [0.3.0]

### Added
- **Off-hours page analysis** — `off_hours_report()` measures how many pages fired outside
  business hours (default 09:00–18:00, Mon–Fri, configurable) and ranks the worst offending
  rules — the biggest on-call-burnout driver. `summary()` gains `off_hours_rate` and the CLI
  shows it; `recommendations()` flags rules that page mostly off-hours for re-routing.
  Times use each alert's own timestamp zone (no conversion — zero dependencies, 3.8-safe).

## [0.2.0]

### Added
- **Per-rule noise score** — `rule_report()` returns `RuleStats` per rule
  (count, ack rate, self-resolve rate, MTTR, `noise_score`) ranked worst-first.
  The score weights the volume of *unacknowledged* alerts up when they
  self-resolve, so it surfaces low-signal rules rather than just high-volume ones.
- **Severity analysis** — `severity_breakdown()` (count + ack/self-resolve rate
  per severity) and a **severity-inflation** recommendation when most
  high-severity alerts self-resolve without an ack.
- `summary()` now includes `by_severity` and `top_noise`; the CLI prints the
  severity breakdown and the noise-score ranking.

## [0.1.0]

### Added
- Alert model + loader, noisiest rules, rolling-window flapping detection,
  MTTA/MTTR, ack rate, self-resolve rate, tuning recommendations, and an
  `alertfatigue` CLI (`--json`, `--fail-on-recommendations`).
