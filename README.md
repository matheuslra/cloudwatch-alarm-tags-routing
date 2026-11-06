# Route CloudWatch alarms on their tags

Sample code for the blog post [Alarm Tags Are Now Part of Your Paging Path](https://matheusarrais.com/blog/cloudwatch-alarm-tags-routing/).

CloudWatch alarms can now carry their tags into EventBridge, SNS and Lambda payloads. This repo deploys tagged alarms with propagation on, and replaces a routing function and its lookup table with one EventBridge rule per team, plus catch-alls for the alarms that would otherwise page nobody. The teams and topics are an example.

| Alarm event | Rule | Goes to |
| --- | --- | --- |
| `Team=payments`, `Environment=prod` | `PaymentsRule` | Payments topic |
| `Team=search`, `Environment=prod` | `SearchRule` | Search topic |
| A `Team` value no rule handles, such as a typo | `UnknownTeamRule` | Unrouted topic |
| No `Team` tag, propagation off, or tags unreadable | `NoTeamTagRule` | Unrouted topic |

A known team with a different `Environment` matches no rule, so it pages nobody. Change that if you want those alarms routed.

## What gets deployed

The same stack is here three times. Pick one:

| Path | Tool |
| --- | --- |
| `cloudformation/template.yaml` | CloudFormation |
| `cdk/` | AWS CDK in TypeScript |
| `terraform/` | Terraform. The alarms use the `awscc` provider, because the `aws` provider doesn't support tag propagation yet |

Each one creates:

- **Three demo alarms** on metrics that get no data, so they stay in `OK` until you change their state. Each one sends `Team` and `Environment` in its events. `sample-checkout-errors` also has a `CostCenter` tag, which the include list keeps out of the payload. `sample-typo-team` is tagged `Team=paymnets`.
- **Three SNS topics and four EventBridge rules,** with a topic policy that only lets these rules publish.
- **An email subscription on each topic,** if you give an address, so you can read the events.

## Deploy

This creates real resources, and alarms have a cost. As soon as it's deployed, `NoTeamTagRule` also matches every alarm in the account that doesn't propagate tags. In a busy account, expect the unrouted topic to get messages from your existing alarms.

**CloudFormation:**

```bash
aws cloudformation deploy --stack-name sample-alarm-routing --template-file cloudformation/template.yaml \
  --parameter-overrides NotificationEmail=you@example.com
```

**CDK:**

```bash
cd cdk && npm ci && npx cdk deploy -c notificationEmail=you@example.com
```

`cdk synth` warns that `ActionConfiguration` isn't in its bundled schema. CloudFormation accepts it, so you can ignore the warning.

**Terraform:**

```bash
cd terraform && terraform init && terraform apply -var notification_email=you@example.com
```

Confirm the three subscription emails SNS sends you.

## Fire an alarm

```bash
aws cloudwatch set-alarm-state --alarm-name sample-checkout-errors \
  --state-value ALARM --state-reason "Testing tag routing"
aws cloudwatch set-alarm-state --alarm-name sample-typo-team \
  --state-value ALARM --state-reason "Testing the catch-all"
```

The first event arrives on the payments topic with `"alarmTags": {"Team": "payments", "Environment": "prod"}`, and no `CostCenter`. The second arrives on the unrouted topic. Each alarm goes back to `OK` at its next evaluation.

## Find the alarms that can't be routed yet

Before you rely on tag routing, count how many of your alarms already carry an owner. This lists every alarm that has propagation off, is missing `Team` or `Environment`, or filters them out of the payload. It only reads, and it exits 1 when it finds any, so you can run it on a schedule:

```bash
pip install -r scripts/requirements.txt
python scripts/audit_alarms.py
```

## Before you use it

- **SNS shares tags with every subscriber,** including email and HTTPS endpoints. These alarms use an include list so only `Team` and `Environment` leave.
- **Tags starting with `aws:` are never propagated.**
- **Retagging an alarm changes where its next page goes,** so treat tag changes like changes to your paging rules.
- **Add each new team twice:** give it a rule, and add it to `UnknownTeamRule`, or its pages also go to the unrouted topic.
- **Creating an alarm with propagation on needs `cloudwatch:ListTagsForResource` on it.** The `cloudwatch:AlarmTagsPropagationEnabled` condition key controls who can turn propagation on.

## Clean up

```bash
aws cloudformation delete-stack --stack-name sample-alarm-routing   # CloudFormation
npx cdk destroy                                                      # CDK, from cdk/
terraform destroy                                                    # Terraform, from terraform/
```

## What was tested

- CI lints the CloudFormation template, synthesizes the CDK app and validates the Terraform on every push. AWS's `ValidateTemplate` API accepted the template.
- The four rule patterns passed eight routing cases against EventBridge's `TestEventPattern` API, using an event modeled on the AWS docs.
- I haven't deployed these stacks or fired a real alarm through them, so try them in a test account first.

## Learn more

- [Alarm tags in action payloads](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarm-tags-in-notifications.html)
- [Alarm events and EventBridge](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-and-eventbridge.html)
- [What's New announcement](https://aws.amazon.com/about-aws/whats-new/2026/10/amazon-cloudwatch-tags-on-alarm-actions-payload/)

This is sample code for learning, not an official AWS project. Review it before you use it in your environment.

## License

[MIT-0](LICENSE)
