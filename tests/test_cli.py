import json
from datetime import datetime, timedelta, timezone
from alertfatigue.cli import main

BASE = datetime(2026, 6, 1, tzinfo=timezone.utc)


def _records():
    # CPUHigh flaps 6x in 30 min, each self-resolving without an ack.
    recs = []
    for i in range(6):
        t = BASE + timedelta(minutes=i * 5)
        recs.append({"rule": "CPUHigh", "opened_at": t.isoformat(),
                     "resolved_at": (t + timedelta(minutes=1)).isoformat()})
    return recs


def test_cli_text_summary(tmp_path, capsys):
    f = tmp_path / "alerts.json"
    f.write_text(json.dumps(_records()))
    code = main([str(f)])
    out = capsys.readouterr().out
    assert code == 0
    assert "Alert summary" in out and "CPUHigh" in out
    assert "Recommendations:" in out


def test_cli_json(tmp_path, capsys):
    f = tmp_path / "alerts.json"
    f.write_text(json.dumps(_records()))
    assert main([str(f), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "summary" in data and "recommendations" in data


def test_cli_fail_on_recommendations(tmp_path):
    f = tmp_path / "alerts.json"
    f.write_text(json.dumps(_records()))
    assert main([str(f), "--fail-on-recommendations"]) == 1


def test_cli_rejects_non_array(tmp_path, capsys):
    f = tmp_path / "bad.json"
    f.write_text('{"not": "a list"}')
    assert main([str(f)]) == 2
    assert "expected a JSON array" in capsys.readouterr().err
