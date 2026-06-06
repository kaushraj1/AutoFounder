# messaging module (AF-017)

AWS-native event/messaging plumbing for the AutoFounder AI orchestrator (the
plumbing the merged orchestrator from PR #12 actually uses): an EventBridge
custom bus + rule, per-pillar SQS work queues each with a dead-letter queue, a
dedicated gate-decisions queue + DLQ, and an SNS notification topic.

## What it creates

| Resource | Notes |
|---|---|
| SQS work queues (1/pillar) | `${name_prefix}-<pillar>`; AWS-managed SSE; 14-day retention |
| SQS dead-letter queues (1/pillar) | `${name_prefix}-<pillar>-dlq`; redrive `maxReceiveCount=5` from its main queue |
| SQS `gate-decisions` queue + DLQ | EventBridge target for gate decisions; same SSE/retention/redrive |
| SQS queue policy (gate-decisions) | Allows only `events.amazonaws.com` (SourceArn = the rule) to `SendMessage` |
| SNS topic | `${name_prefix}-notifications`; encrypted via `sns_kms_master_key_id` |
| EventBridge bus | custom bus named `${name_prefix}` |
| EventBridge rule | matches detail-type `gate.required` on the bus |
| EventBridge target | routes the rule to the `gate-decisions` SQS queue |

All SQS queues use **AWS-managed SSE** (`sqs_managed_sse_enabled = true`) — encryption
at rest with no CMK key policy to maintain. The SNS topic defaults to the
AWS-managed SNS key (`alias/aws/sns`); pass the platform CMK alias for stricter
control. **No secret values are written to Terraform state by this module.**

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `name_prefix` | string | — | Resource name prefix, e.g. `autofounder-ai-staging`. |
| `pillar_queue_names` | list(string) | `["strategy","research","product-planner","architect","coder","reviewer","devops","marketing","llmops"]` | Per-pillar work queue base names; each gets a main queue + DLQ. |
| `sns_kms_master_key_id` | string | `alias/aws/sns` | KMS key id/alias for SNS SSE. |
| `tags` | map(string) | `{}` | Extra tags (the 4 platform tags come from provider `default_tags`). |

## Outputs

`queue_urls` (map, incl. `gate-decisions`), `queue_arns` (map), `dlq_arns` (map),
`sns_topic_arn`, `event_bus_name`, `event_bus_arn`, `gate_decisions_queue_url`.

## Design notes

- **DLQ per queue.** Each main queue redrives to its own DLQ at
  `maxReceiveCount=5` so a poison message can't block its pillar's throughput;
  DLQs retain for the SQS max (14 days) for inspection/replay.
- **Gate routing.** The orchestrator publishes a `gate.required` event to the
  custom bus; the rule delivers it to the `gate-decisions` queue. The queue
  policy is scoped by `aws:SourceArn` to that exact rule (confused-deputy
  mitigation) — no broad `events.amazonaws.com` grant.
- **SNS encryption.** Override `sns_kms_master_key_id` with the platform CMK
  alias (from the secrets module) where a customer-managed key is required.

## Deferred: Confluent Kafka

Confluent Cloud / Kafka is **intentionally NOT provisioned here**. It requires
the `confluentinc/confluent` provider and a Confluent Cloud account, which would
add a non-AWS provider and external credentials to this module. The AWS-native
surface above is what the orchestrator uses today; add Confluent in a separate
module/task if/when a Kafka requirement is confirmed.
