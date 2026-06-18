"""alertfatigue: find noisy, flapping, and self-resolving alerts in your history."""
from .model import Alert, load_alerts
from .analyze import (noisiest, flapping_rules, mtta, mttr, ack_rate,
                      self_resolve_rate, rule_report, RuleStats, severity_breakdown,
                      recommendations, summary)
__all__ = ["Alert", "load_alerts", "noisiest", "flapping_rules", "mtta", "mttr",
           "ack_rate", "self_resolve_rate", "rule_report", "RuleStats",
           "severity_breakdown", "recommendations", "summary"]
__version__ = "0.2.0"
