output "queue_urls" {
  description = "Map of work queue name -> SQS queue URL (includes gate-decisions)."
  value       = { for k, q in aws_sqs_queue.main : k => q.url }
}

output "queue_arns" {
  description = "Map of work queue name -> SQS queue ARN (includes gate-decisions)."
  value       = { for k, q in aws_sqs_queue.main : k => q.arn }
}

output "dlq_arns" {
  description = "Map of work queue name -> dead-letter queue ARN."
  value       = { for k, q in aws_sqs_queue.dlq : k => q.arn }
}

output "sns_topic_arn" {
  description = "ARN of the notifications SNS topic."
  value       = aws_sns_topic.this.arn
}

output "event_bus_name" {
  description = "Name of the EventBridge custom bus."
  value       = aws_cloudwatch_event_bus.this.name
}

output "event_bus_arn" {
  description = "ARN of the EventBridge custom bus."
  value       = aws_cloudwatch_event_bus.this.arn
}

output "gate_decisions_queue_url" {
  description = "URL of the gate-decisions SQS queue (EventBridge gate.required target)."
  value       = aws_sqs_queue.main["gate-decisions"].url
}
