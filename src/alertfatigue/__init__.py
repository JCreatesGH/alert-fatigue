"""alertfatigue: find noisy, flapping, and self-resolving alerts in your history."""
from .model import Alert, load_alerts
from .analyze import (noisiest, flapping_rules, mtta, self_resolve_rate,
                      recommendations, summary)
__all__ = ["Alert", "load_alerts", "noisiest", "flapping_rules", "mtta",
           "self_resolve_rate", "recommendations", "summary"]
__version__ = "0.1.0"
