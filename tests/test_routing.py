"""Runs with no AWS account. scripts/check_patterns_on_aws.py runs the same cases against EventBridge."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_alarms import audit, problems  # noqa: E402
from create_alarm import alarm_request  # noqa: E402
from routing_cases import CASES, rules  # noqa: E402

MISSING = object()


def value_matches(condition, value):
    if isinstance(condition, dict):
        if "exists" in condition:
            return (value is not MISSING) == condition["exists"]
        if "anything-but" in condition:
            return value is not MISSING and value not in condition["anything-but"]
        raise ValueError(f"unsupported condition: {condition}")
    return value == condition


def pattern_matches(pattern, event):
    """A small stand-in for EventBridge. It only understands what this sample's rules use."""
    for key, expected in pattern.items():
        value = event.get(key, MISSING) if isinstance(event, dict) else MISSING
        if isinstance(expected, dict):
            if not pattern_matches(expected, value if isinstance(value, dict) else {}):
                return False
        elif not any(value_matches(condition, value) for condition in expected):
            return False
    return True


class Routing(unittest.TestCase):
    def test_each_event_reaches_the_expected_rules(self):
        patterns = rules()
        for name, event, expected in CASES:
            with self.subTest(name):
                matched = {rule for rule, pattern in patterns.items() if pattern_matches(pattern, event)}
                self.assertEqual(matched, expected)


class FakeCloudWatch:
    def __init__(self, alarms, tags):
        self.alarms, self.tags = alarms, tags

    def get_paginator(self, _):
        return self

    def paginate(self, **_):
        return [{"MetricAlarms": self.alarms, "CompositeAlarms": []}]

    def list_tags_for_resource(self, ResourceARN):
        return {"Tags": self.tags[ResourceARN]}


TAGS = [{"Key": "Team", "Value": "payments"}, {"Key": "Environment", "Value": "prod"}]


class Audit(unittest.TestCase):
    def test_a_good_alarm_has_no_problems(self):
        alarm = {"ActionConfiguration": alarm_request("a", "payments", "prod")["ActionConfiguration"]}
        self.assertEqual(problems(alarm, TAGS), [])

    def test_propagation_off_and_a_missing_tag_are_reported(self):
        self.assertEqual(problems({}, TAGS[:1]), ["tag propagation is off", "missing tags: Environment"])

    def test_a_required_tag_filtered_from_the_payload_is_reported(self):
        included = {"ActionConfiguration": {"AlarmTagsPropagation": {"Enabled": True, "IncludedTagKeys": ["Team"]}}}
        excluded = {"ActionConfiguration": {"AlarmTagsPropagation": {"Enabled": True, "ExcludedTagKeys": ["Team"]}}}
        self.assertEqual(problems(included, TAGS), ["filtered from the payload: Environment"])
        self.assertEqual(problems(excluded, TAGS), ["filtered from the payload: Team"])

    def test_audit_walks_every_alarm(self):
        client = FakeCloudWatch([{"AlarmName": "a", "AlarmArn": "arn:a"}], {"arn:a": TAGS})
        self.assertEqual(audit(client), [("a", "tag propagation is off")])


if __name__ == "__main__":
    unittest.main()
