# AWS CDK version (TypeScript)

The same stack as the CloudFormation version, written as a CDK app. `lib/stack.ts` defines the resources and `bin/app.ts` reads the settings. It deploys as the stack `sample-alarm-routing`.

## Before you start

- Node.js and npm. CI uses Node.js 24.
- A CDK-bootstrapped account and Region. If you've never used CDK there, run this once:

  ```bash
  cd cdk && npm ci && npx cdk bootstrap
  ```

## Deploy

```bash
cd cdk
npm ci
npx cdk diff      # optional: see what will be created
npx cdk deploy -c notificationEmail=you@example.com
```

| Context key | Default | What it does |
| --- | --- | --- |
| `notificationEmail` | none | Optional. Subscribes this address to all three topics so you can read the events |
| `environment` | `prod` | The `Environment` tag on the demo alarms, and the value the team rules match |

The alarms are `CfnAlarm` resources with `actionConfiguration.alarmTagsPropagation` set. `cdk synth` and `cdk deploy` warn that `ActionConfiguration` isn't in CDK's bundled CloudFormation schema yet. CloudFormation accepts the property, so you can ignore the warning.

If you give an address, confirm the three subscription emails SNS sends you.

## Outputs

`npx cdk deploy` prints `PaymentsTopicArn`, `SearchTopicArn` and `UnroutedTopicArn` when it finishes. Then [fire an alarm](../README.md#fire-an-alarm).

## Clean up

From `cdk/`:

```bash
npx cdk destroy
```
