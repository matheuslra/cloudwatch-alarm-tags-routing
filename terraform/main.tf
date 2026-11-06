# Alarms that carry their tags into EventBridge, one rule per team on alarmTags.Team,
# and catch-alls for alarms that match no team.

locals {
  # Demo alarms. Fire one with: aws cloudwatch set-alarm-state --state-value ALARM ...
  # Only Team and Environment leave in the payload. CostCenter stays behind, because SNS shares tags with every subscriber.
  alarms = {
    checkout_errors = {
      name                = "sample-checkout-errors"
      description         = "Demo alarm owned by payments"
      metric_name         = "CheckoutErrors"
      statistic           = "Sum"
      threshold           = 1
      comparison_operator = "GreaterThanOrEqualToThreshold"
      tags                = { Team = "payments", Environment = var.environment, CostCenter = "cc-1234" }
    }
    search_latency = {
      name                = "sample-search-latency"
      description         = "Demo alarm owned by search"
      metric_name         = "SearchLatency"
      statistic           = "Average"
      threshold           = 500
      comparison_operator = "GreaterThanThreshold"
      tags                = { Team = "search", Environment = var.environment }
    }
    # The Team tag has a typo, so no team rule matches and the unknown-team rule catches it.
    typo_team = {
      name                = "sample-typo-team"
      description         = "Demo alarm with a misspelled Team tag"
      metric_name         = "RefundErrors"
      statistic           = "Sum"
      threshold           = 1
      comparison_operator = "GreaterThanOrEqualToThreshold"
      tags                = { Team = "paymnets", Environment = var.environment }
    }
  }

  alarm_in_state = {
    source        = ["aws.cloudwatch"]
    "detail-type" = ["CloudWatch Alarm State Change"]
  }

  rules = {
    payments = {
      description = "Alarms owned by payments"
      topic       = "payments"
      pattern = jsonencode(merge(local.alarm_in_state, {
        detail = { state = { value = ["ALARM"] }, alarmTags = { Team = ["payments"], Environment = [var.environment] } }
      }))
    }
    search = {
      description = "Alarms owned by search"
      topic       = "search"
      pattern = jsonencode(merge(local.alarm_in_state, {
        detail = { state = { value = ["ALARM"] }, alarmTags = { Team = ["search"], Environment = [var.environment] } }
      }))
    }
    # Also catches alarms without propagation, and events whose tags CloudWatch couldn't read.
    no_team_tag = {
      description = "Alarms with no Team tag in the event"
      topic       = "unrouted"
      pattern = jsonencode(merge(local.alarm_in_state, {
        detail = { state = { value = ["ALARM"] }, alarmTags = { Team = [{ exists = false }] } }
      }))
    }
    # Add each new team here as well as giving it a rule above, or its pages go to both.
    unknown_team = {
      description = "Alarms with a Team tag no rule handles, such as a typo"
      topic       = "unrouted"
      pattern = jsonencode(merge(local.alarm_in_state, {
        detail = { state = { value = ["ALARM"] }, alarmTags = { Team = [{ "anything-but" = ["payments", "search"] }] } }
      }))
    }
  }
}

resource "awscc_cloudwatch_alarm" "demo" {
  for_each            = local.alarms
  alarm_name          = each.value.name
  alarm_description   = each.value.description
  namespace           = "Sample/AlarmTags"
  metric_name         = each.value.metric_name
  statistic           = each.value.statistic
  period              = 300
  evaluation_periods  = 1
  threshold           = each.value.threshold
  comparison_operator = each.value.comparison_operator
  treat_missing_data  = "notBreaching"
  tags                = [for key, value in each.value.tags : { key = key, value = value }]

  action_configuration = {
    alarm_tags_propagation = {
      enabled           = true
      included_tag_keys = ["Team", "Environment"]
    }
  }
}

# The unrouted topic should go somewhere a person looks every day. An unmatched event is the new unmapped alarm.
resource "aws_sns_topic" "this" {
  for_each = toset(["payments", "search", "unrouted"])
  name     = "sample-alarm-routing-${each.key}"
}

resource "aws_cloudwatch_event_rule" "this" {
  for_each      = local.rules
  name          = "sample-alarm-routing-${replace(each.key, "_", "-")}"
  description   = each.value.description
  event_pattern = each.value.pattern
}

resource "aws_cloudwatch_event_target" "this" {
  for_each  = local.rules
  rule      = aws_cloudwatch_event_rule.this[each.key].name
  target_id = each.value.topic
  arn       = aws_sns_topic.this[each.value.topic].arn
}

# Only this stack's rules can publish, not EventBridge rules in other accounts.
resource "aws_sns_topic_policy" "this" {
  for_each = aws_sns_topic.this
  arn      = each.value.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sns:Publish"
      Resource  = each.value.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = [for key, rule in local.rules : aws_cloudwatch_event_rule.this[key].arn if rule.topic == each.key]
        }
      }
    }]
  })
}

resource "aws_sns_topic_subscription" "email" {
  for_each  = var.notification_email == "" ? {} : aws_sns_topic.this
  topic_arn = each.value.arn
  protocol  = "email"
  endpoint  = var.notification_email
}
