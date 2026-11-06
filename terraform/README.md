# Terraform version

The same stack as the CloudFormation version, in Terraform. It uses two providers: `hashicorp/awscc` (1.109 or later) for the three alarms, because the `aws` provider can't set tag propagation yet, and `hashicorp/aws` for the SNS topics, the EventBridge rules and targets, the topic policies and the email subscriptions.

## Before you start

- Terraform 1.6 or later.
- AWS credentials for the target account, for example `export AWS_PROFILE=my-test-account`.

## Deploy

```bash
cd terraform
terraform init
terraform plan    # optional: see what will be created
terraform apply -var notification_email=you@example.com
```

| Variable | Default | What it does |
| --- | --- | --- |
| `region` | `us-east-1` | Where to deploy. Tag propagation isn't available in Middle East (UAE) or Middle East (Bahrain) |
| `notification_email` | empty | Optional. Subscribes this address to all three topics so you can read the events |
| `environment` | `prod` | The `Environment` tag on the demo alarms, and the value the team rules match |

Each topic's policy lets only the rules that target that topic publish to it. If you give an address, confirm the three subscription emails SNS sends you.

## Outputs

```bash
terraform output topic_arns
```

Then [fire an alarm](../README.md#fire-an-alarm).

## Clean up

From `terraform/`:

```bash
terraform destroy
```
