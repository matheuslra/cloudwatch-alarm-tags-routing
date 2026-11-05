#!/usr/bin/env python3
"""Create a metric alarm with ownership tags and turn on tag propagation.

Only the keys in IncludedTagKeys reach the payload. The alarm needs no action, because EventBridge
receives its state changes by default. CloudWatch alarms have a cost.
"""
import argparse

import boto3

ROUTING_TAG_KEYS = ["Team", "Environment"]


def alarm_request(name, team, environment):
    return {
        "AlarmName": name,
        "Namespace": "Sample/Checkout",
        "MetricName": "Errors",
        "Statistic": "Sum",
        "Period": 60,
        "EvaluationPeriods": 1,
        "Threshold": 1,
        "ComparisonOperator": "GreaterThanOrEqualToThreshold",
        "TreatMissingData": "notBreaching",
        "Tags": [{"Key": "Team", "Value": team}, {"Key": "Environment", "Value": environment}],
        "ActionConfiguration": {"AlarmTagsPropagation": {"Enabled": True, "IncludedTagKeys": ROUTING_TAG_KEYS}},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--team", required=True)
    parser.add_argument("--environment", default="prod")
    args = parser.parse_args()
    boto3.client("cloudwatch").put_metric_alarm(**alarm_request(args.name, args.team, args.environment))
    print(f"Created {args.name}. Its state changes now carry Team and Environment.")


if __name__ == "__main__":
    main()
