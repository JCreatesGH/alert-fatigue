# Changelog

All notable changes are documented here, following
[Keep a Changelog](https://keepachangelog.com/) and [SemVer](https://semver.org/).

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
