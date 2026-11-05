#!/usr/bin/env python3
"""List alarms that can't be routed: no propagation, or missing a required tag. Reads only.

It exits 1 when it finds any, so you can run it on a schedule to catch alarms someone created by hand.
"""
import boto3

REQUIRED_TAGS = {"Team", "Environment"}


def problems(alarm, tags):
    config = alarm.get("ActionConfiguration", {}).get("AlarmTagsPropagation", {})
    found = []
    if not config.get("Enabled"):
        found.append("tag propagation is off")
    missing = REQUIRED_TAGS - {tag["Key"] for tag in tags}
    if missing:
        found.append(f"missing tags: {', '.join(sorted(missing))}")
    included, excluded = config.get("IncludedTagKeys"), config.get("ExcludedTagKeys")
    filtered = REQUIRED_TAGS - set(included) if included else REQUIRED_TAGS & set(excluded or [])
    if config.get("Enabled") and filtered:
        found.append(f"filtered from the payload: {', '.join(sorted(filtered))}")
    return found


def audit(client):
    paginator = client.get_paginator("describe_alarms")
    pages = paginator.paginate(AlarmTypes=["MetricAlarm", "CompositeAlarm"])
    report = []
    for page in pages:
        for alarm in page.get("MetricAlarms", []) + page.get("CompositeAlarms", []):
            tags = client.list_tags_for_resource(ResourceARN=alarm["AlarmArn"])["Tags"]
            report.extend((alarm["AlarmName"], problem) for problem in problems(alarm, tags))
    return report


if __name__ == "__main__":
    results = audit(boto3.client("cloudwatch"))
    for name, problem in results:
        print(f"{name}: {problem}")
    print(f"{len(results)} problem(s)")
    raise SystemExit(1 if results else 0)
