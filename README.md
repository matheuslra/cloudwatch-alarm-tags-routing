# Route CloudWatch alarms on their tags

Sample code for the blog post [Alarm Tags Are Now Part of Your Paging Path](https://matheusarrais.com/blog/cloudwatch-alarm-tags-routing/).

CloudWatch alarms can now carry their tags into EventBridge, SNS and Lambda payloads. This repo replaces a routing function and its lookup table with one EventBridge rule per team, plus catch-alls for the alarms that would otherwise page nobody. The teams and topics are an example.

| Alarm event | Rule | Goes to |
| --- | --- | --- |
| `Team=payments`, `Environment=prod` | `PaymentsRule` | Payments topic |
| `Team=search`, `Environment=prod` | `SearchRule` | Search topic |
| A `Team` value no rule handles, such as a typo | `UnknownTeamRule` | Unrouted topic |
| No `Team` tag, propagation off, or tags unreadable | `NoTeamTagRule` | Unrouted topic |

A known team with a different `Environment` matches no rule, so it pages nobody. Change that if you want those alarms routed.

## What's here

| Path | What it does |
| --- | --- |
| `infra/routing.yaml` | CloudFormation for the rules and SNS topics |
| `scripts/create_alarm.py` | Creates an alarm with tags and propagation on |
| `scripts/audit_alarms.py` | Lists alarms that can't be routed. It only reads |
| `scripts/check_patterns_on_aws.py` | Runs the routing cases against EventBridge. It creates nothing |
| `tests/` | The routing cases and offline tests |

## Try it with no AWS account

```bash
pip install -r tests/requirements.txt -r scripts/requirements.txt
python -m unittest discover -s tests -v
```

The offline tests use a small stand-in for EventBridge matching, so it only understands what these rules use.

## Test it against AWS

These create nothing in your account:

```bash
python scripts/check_patterns_on_aws.py
python scripts/audit_alarms.py
```

## Deploy it

This creates real resources, and alarms have a cost. The topics have no subscribers until you add them.

```bash
aws cloudformation deploy --stack-name sample-alarm-routing --template-file infra/routing.yaml
python scripts/create_alarm.py --name checkout-errors --team payments
```

Creating an alarm with propagation on needs `cloudwatch:ListTagsForResource` on it. The `cloudwatch:AlarmTagsPropagationEnabled` condition key controls who can turn propagation on.

## What was tested

- `check_patterns_on_aws.py` passed all eight routing cases against EventBridge's `TestEventPattern` API.
- The sample event is modeled on the AWS docs. I have not deployed the stack or fired a real alarm through it, so a real event hasn't reached a real topic.

## Before you use it

- **SNS shares tags with every subscriber,** including email and HTTPS endpoints. `create_alarm.py` uses an include list so only `Team` and `Environment` leave.
- **Tags starting with `aws:` are never propagated.**
- **Retagging an alarm changes where its next page goes,** so treat tag changes like changes to your paging rules.
- **Add each new team twice:** give it a rule, and add it to `UnknownTeamRule`, or its pages also go to the unrouted topic.

## Security checks

The `Security` workflow runs on every push to `main`, on pull requests, weekly, and on demand. None of its jobs needs an API key or AWS access.

- **Secret scan:** gitleaks checks the full git history on every run.
- **Code scan:** CodeQL checks the Python code and the GitHub Actions workflows, and fails on any finding.
- **Smoke test:** runs the offline tests.

Changes are also reviewed with Claude Code's [`/security-review`](https://support.claude.com/en/articles/11932705-automated-security-reviews-in-claude-code) before they're pushed.

These checks add to human review and don't replace it. They can't tell you the sample is safe for your environment.

## Learn more

- [Alarm tags in action payloads](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarm-tags-in-notifications.html)
- [Alarm events and EventBridge](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-and-eventbridge.html)
- [What's New announcement](https://aws.amazon.com/about-aws/whats-new/2026/10/amazon-cloudwatch-tags-on-alarm-actions-payload/)

This is sample code for learning, not an official AWS project.

## License

[MIT-0](LICENSE)
