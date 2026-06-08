# ---------------------------------------------------------------------------
# Messaging (AF-017) — AWS-native event/messaging plumbing used by the merged
# orchestrator (PR #12): an EventBridge custom bus + rule routing gate events,
# per-pillar SQS work queues each paired with a DLQ, a dedicated gate-decisions
# queue + DLQ, and an SNS topic for fan-out notifications.
#
# All SQS queues use AWS-managed SSE (sqs_managed_sse_enabled) — encryption at
# rest with no CMK key-policy to maintain. The SNS topic is encrypted with the
# key referenced by var.sns_kms_master_key_id. No secret values are written to
# state by this module.
#
# DEFERRED: Confluent Cloud / Kafka. It requires the confluentinc/confluent
# provider plus a Confluent Cloud account and is intentionally NOT wired here —
# see README.md. This module covers only the AWS-native messaging surface.
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_partition" "current" {}

locals {
  # Every work queue that gets a main + DLQ pair: the pillar queues plus the
  # dedicated gate-decisions queue.
  work_queue_names = concat(var.pillar_queue_names, ["gate-decisions"])

  message_retention_seconds = 1209600 # 14 days (SQS max)
  dlq_max_receive_count     = 5
}

# --- SQS: dead-letter queues (created first so mains can reference their ARN) -

resource "aws_sqs_queue" "dlq" {
  for_each = toset(local.work_queue_names)

  name                      = "${var.name_prefix}-${each.value}-dlq"
  sqs_managed_sse_enabled   = true
  message_retention_seconds = local.message_retention_seconds

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.value}-dlq"
  })
}

# --- SQS: main work queues (each redrives failed messages to its own DLQ) -----

resource "aws_sqs_queue" "main" {
  for_each = toset(local.work_queue_names)

  name                      = "${var.name_prefix}-${each.value}"
  sqs_managed_sse_enabled   = true
  message_retention_seconds = local.message_retention_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq[each.value].arn
    maxReceiveCount     = local.dlq_max_receive_count
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.value}"
  })
}

# --- SNS: notification fan-out topic (encrypted at rest) ----------------------

resource "aws_sns_topic" "this" {
  name              = "${var.name_prefix}-notifications"
  kms_master_key_id = var.sns_kms_master_key_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-notifications"
  })
}

# --- EventBridge: custom bus + gate.required rule -> gate-decisions queue ------

resource "aws_cloudwatch_event_bus" "this" {
  name = var.name_prefix

  tags = merge(var.tags, {
    Name = var.name_prefix
  })
}

resource "aws_cloudwatch_event_rule" "gate_required" {
  name           = "${var.name_prefix}-gate-required"
  description    = "Route gate.required events to the gate-decisions SQS queue."
  event_bus_name = aws_cloudwatch_event_bus.this.name

  event_pattern = jsonencode({
    detail-type = ["gate.required"]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-gate-required"
  })
}

resource "aws_cloudwatch_event_target" "gate_decisions" {
  rule           = aws_cloudwatch_event_rule.gate_required.name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  target_id      = "${var.name_prefix}-gate-decisions"
  arn            = aws_sqs_queue.main["gate-decisions"].arn
}

# Allow only this rule (SourceArn) to deliver to the gate-decisions queue.
data "aws_iam_policy_document" "gate_decisions_queue" {
  statement {
    sid       = "AllowEventBridgeSendMessage"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.main["gate-decisions"].arn]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.gate_required.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "gate_decisions" {
  queue_url = aws_sqs_queue.main["gate-decisions"].id
  policy    = data.aws_iam_policy_document.gate_decisions_queue.json
}
