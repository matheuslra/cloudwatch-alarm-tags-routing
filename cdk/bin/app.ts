import { App } from 'aws-cdk-lib';
import { AlarmRoutingStack } from '../lib/stack';

const app = new App();

// Override with -c environment=staging or -c notificationEmail=you@example.com.
new AlarmRoutingStack(app, 'AlarmTagsRouting', {
  stackName: 'sample-alarm-routing',
  alarmEnvironment: app.node.tryGetContext('environment') ?? 'prod',
  notificationEmail: app.node.tryGetContext('notificationEmail'),
});
