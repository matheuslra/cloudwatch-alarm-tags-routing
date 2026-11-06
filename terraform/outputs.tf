output "topic_arns" {
  value = { for name, topic in aws_sns_topic.this : name => topic.arn }
}
