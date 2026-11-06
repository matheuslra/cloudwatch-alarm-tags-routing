# CloudFormation version

One template, `template.yaml`, deployed with the AWS CLI. It creates everything listed in the [main README](../README.md#what-gets-deployed): the three tagged demo alarms, the three SNS topics, the four EventBridge rules, the topic policy and the optional email subscriptions.

## Deploy

```bash
aws cloudformation deploy --stack-name sample-alarm-routing \
  --template-file cloudformation/template.yaml \
  --parameter-overrides NotificationEmail=you@example.com
```

| Parameter | Default | What it does |
| --- | --- | --- |
| `NotificationEmail` | empty | Optional. Subscribes this address to all three topics so you can read the events |
| `Environment` | `prod` | The `Environment` tag on the demo alarms, and the value the team rules match |

If you give an address, confirm the three subscription emails SNS sends you. Tag propagation is set on each alarm under `ActionConfiguration.AlarmTagsPropagation`.

## Outputs

`PaymentsTopicArn`, `SearchTopicArn` and `UnroutedTopicArn`:

```bash
aws cloudformation describe-stacks --stack-name sample-alarm-routing --query 'Stacks[0].Outputs' --output table
```

Then [fire an alarm](../README.md#fire-an-alarm).

## Clean up

```bash
aws cloudformation delete-stack --stack-name sample-alarm-routing
aws cloudformation wait stack-delete-complete --stack-name sample-alarm-routing
```

This also removes the email subscriptions.
