#!/usr/bin/env python3
"""Run the routing cases against EventBridge's TestEventPattern API. It creates nothing."""
import json
import sys
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))

from routing_cases import CASES, rules  # noqa: E402

client = boto3.client("events")
patterns = rules()
failed = 0
for name, event, expected in CASES:
    matched = {
        rule
        for rule, pattern in patterns.items()
        if client.test_event_pattern(EventPattern=json.dumps(pattern), Event=json.dumps(event))["Result"]
    }
    failed += matched != expected
    print("ok  " if matched == expected else "FAIL", name, sorted(matched))
raise SystemExit(1 if failed else 0)
