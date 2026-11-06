import { CfnOutput, Stack, StackProps } from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as events from 'aws-cdk-lib/aws-events';
import * as sns from 'aws-cdk-lib/aws-sns';
import { Construct } from 'constructs';

export interface AlarmRoutingStackProps extends StackProps {
  alarmEnvironment: string;
  notificationEmail?: string;
}

interface DemoAlarm {
  name: string;
  description: string;
  metricName: string;
  statistic: string;
  threshold: number;
  comparisonOperator: string;
  tags: Record<string, string>;
}

// Alarms that carry their tags into EventBridge, one rule per team on alarmTags.Team,
// and catch-alls for alarms that match no team.
export class AlarmRoutingStack extends Stack {
  constructor(scope: Construct, id: string, props: AlarmRoutingStackProps) {
    super(scope, id, props);
    const environment = props.alarmEnvironment;

    // Demo alarms. Fire one with: aws cloudwatch set-alarm-state --state-value ALARM ...
    // Only Team and Environment leave in the payload. CostCenter stays behind, because SNS shares tags with every subscriber.
    const alarms: Record<string, DemoAlarm> = {
      CheckoutErrorsAlarm: {
        name: 'sample-checkout-errors',
        description: 'Demo alarm owned by payments',
        metricName: 'CheckoutErrors',
        statistic: 'Sum',
        threshold: 1,
        comparisonOperator: 'GreaterThanOrEqualToThreshold',
        tags: { Team: 'payments', Environment: environment, CostCenter: 'cc-1234' },
      },
      SearchLatencyAlarm: {
        name: 'sample-search-latency',
        description: 'Demo alarm owned by search',
        metricName: 'SearchLatency',
        statistic: 'Average',
        threshold: 500,
        comparisonOperator: 'GreaterThanThreshold',
        tags: { Team: 'search', Environment: environment },
      },
      // The Team tag has a typo, so no team rule matches and the unknown-team rule catches it.
      TypoTeamAlarm: {
        name: 'sample-typo-team',
        description: 'Demo alarm with a misspelled Team tag',
        metricName: 'RefundErrors',
        statistic: 'Sum',
        threshold: 1,
        comparisonOperator: 'GreaterThanOrEqualToThreshold',
        tags: { Team: 'paymnets', Environment: environment },
      },
    };
    for (const [alarmId, alarm] of Object.entries(alarms)) {
      new cloudwatch.CfnAlarm(this, alarmId, {
        alarmName: alarm.name,
        alarmDescription: alarm.description,
        namespace: 'Sample/AlarmTags',
        metricName: alarm.metricName,
        statistic: alarm.statistic,
        period: 300,
        evaluationPeriods: 1,
        threshold: alarm.threshold,
        comparisonOperator: alarm.comparisonOperator,
        treatMissingData: 'notBreaching',
        tags: Object.entries(alarm.tags).map(([key, value]) => ({ key, value })),
        actionConfiguration: {
          alarmTagsPropagation: { enabled: true, includedTagKeys: ['Team', 'Environment'] },
        },
      });
    }

    const payments = new sns.Topic(this, 'PaymentsTopic');
    const search = new sns.Topic(this, 'SearchTopic');
    // Send this somewhere a person looks every day. An unmatched event is the new unmapped alarm.
    const unrouted = new sns.Topic(this, 'UnroutedTopic');

    const alarmInState = (alarmTags: Record<string, unknown>) => ({
      source: ['aws.cloudwatch'],
      'detail-type': ['CloudWatch Alarm State Change'],
      detail: { state: { value: ['ALARM'] }, alarmTags },
    });
    const rule = (ruleId: string, description: string, alarmTags: Record<string, unknown>, topic: sns.Topic, targetId: string) =>
      new events.CfnRule(this, ruleId, {
        description,
        eventPattern: alarmInState(alarmTags),
        targets: [{ id: targetId, arn: topic.topicArn }],
      });

    const rules = [
      rule('PaymentsRule', 'Alarms owned by payments', { Team: ['payments'], Environment: [environment] }, payments, 'payments'),
      rule('SearchRule', 'Alarms owned by search', { Team: ['search'], Environment: [environment] }, search, 'search'),
      // Also catches alarms without propagation, and events whose tags CloudWatch couldn't read.
      rule('NoTeamTagRule', 'Alarms with no Team tag in the event', { Team: [{ exists: false }] }, unrouted, 'unrouted'),
      // Add each new team here as well as giving it a rule above, or its pages go to both.
      rule('UnknownTeamRule', 'Alarms with a Team tag no rule handles, such as a typo',
        { Team: [{ 'anything-but': ['payments', 'search'] }] }, unrouted, 'unrouted'),
    ];

    const topics = [payments, search, unrouted];
    new sns.CfnTopicPolicy(this, 'TopicPolicy', {
      topics: topics.map((topic) => topic.topicArn),
      policyDocument: {
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: { Service: 'events.amazonaws.com' },
          Action: 'sns:Publish',
          Resource: topics.map((topic) => topic.topicArn),
          // Only this stack's rules can publish, not EventBridge rules in other accounts.
          Condition: { ArnEquals: { 'aws:SourceArn': rules.map((r) => r.attrArn) } },
        }],
      },
    });

    if (props.notificationEmail) {
      topics.forEach((topic, index) => new sns.CfnSubscription(this, `Email${index}`, {
        topicArn: topic.topicArn,
        protocol: 'email',
        endpoint: props.notificationEmail,
      }));
    }

    new CfnOutput(this, 'PaymentsTopicArn', { value: payments.topicArn });
    new CfnOutput(this, 'SearchTopicArn', { value: search.topicArn });
    new CfnOutput(this, 'UnroutedTopicArn', { value: unrouted.topicArn });
  }
}
