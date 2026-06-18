"""Command-line interface: analyze an alert-history JSON export."""
from __future__ import annotations
import argparse
import json
import sys
from typing import List, Optional

from .model import load_alerts
from .analyze import summary, recommendations, rule_report, severity_breakdown


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="alertfatigue", description="Analyze alert history for noise, flapping, and MTTA/MTTR.")
    parser.add_argument("file", nargs="?", help="JSON array of alert records (default: stdin)")
    parser.add_argument("--json", action="store_true", help="emit summary + recommendations as JSON")
    parser.add_argument("--fail-on-recommendations", action="store_true",
                        help="exit 1 if any tuning recommendation is produced (for CI gating)")
    args = parser.parse_args(argv)

    raw = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    try:
        records = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(records, list):
        print("error: expected a JSON array of alert records", file=sys.stderr)
        return 2

    alerts = load_alerts(records)
    s = summary(alerts)
    recs = recommendations(alerts)

    if args.json:
        print(json.dumps({"summary": s, "recommendations": recs}, indent=2, default=str))
    else:
        print("Alert summary")
        print(f"  total:             {s['total']}")
        print(f"  unique rules:      {s['unique_rules']}")
        print(f"  MTTA:              {s['mtta_s']}s")
        print(f"  MTTR:              {s['mttr_s']}s")
        print(f"  ack rate:          {s['ack_rate'] * 100:.1f}%")
        print(f"  self-resolve rate: {s['self_resolve_rate'] * 100:.1f}%")
        print(f"  flapping rules:    {s['flapping_rules']}")
        sev = severity_breakdown(alerts)
        if sev:
            print("  by severity:")
            for name, st in sorted(sev.items(), key=lambda kv: -kv[1]["count"]):
                print(f"    {st['count']:>4}  {name:<10} ({st['self_resolve_rate']*100:.0f}% self-resolved)")
        report = rule_report(alerts, top=5)
        if report:
            print("  noisiest rules (by noise score):")
            for r in report:
                print(f"    {r.noise_score:>7.1f}  {r.rule}  "
                      f"(×{r.count}, ack {r.ack_rate*100:.0f}%, self-resolve {r.self_resolve_rate*100:.0f}%)")
        if recs:
            print("\nRecommendations:")
            for r in recs:
                print(f"  • {r}")
        else:
            print("\nNo tuning recommendations — alerts look healthy.")

    return 1 if (args.fail_on_recommendations and recs) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
