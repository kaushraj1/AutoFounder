# ---------------------------------------------------------------------------
# IAM (AF-019) — least-privilege ECS roles. One shared TASK EXECUTION role
# (pull image, write logs, read injected secrets, decrypt with the CMK) and a
# per-service TASK role (application permissions; deny-by-default until granted).
# No wildcard *:* policies. ECR repos are the account-global shared repos, so
# their ARNs are constructed rather than read from the global stack's state.
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_partition" "current" {}

locals {
  ecr_repository_arns = [
    for name in var.ecr_repository_names :
    "arn:${data.aws_partition.current.partition}:ecr:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:repository/${var.project}/${name}"
  ]

  log_group_prefix = coalesce(var.log_group_prefix, "/ecs/${var.name_prefix}")

  # Scope to this env's ECS log group and its per-service child groups (and
  # their streams) — the explicit ':*' form, not a prefix glob that would also
  # match sibling groups. ECR repos are assumed to be in this same region.
  log_group_arns = [
    "arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:${local.log_group_prefix}:*",
    "arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:${local.log_group_prefix}/*:*",
  ]
}

# Trust policy shared by the execution role and all task roles.
data "aws_iam_policy_document" "ecs_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    # Confused-deputy mitigation: only this account's ECS may assume.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

# --- Task execution role (used by the ECS agent, not the app) ---------------

data "aws_iam_policy_document" "execution" {
  # GetAuthorizationToken has no resource-level scoping in IAM; "*" is required
  # by the API and is NOT an admin wildcard.
  statement {
    sid       = "EcrAuthToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid    = "EcrPull"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]
    resources = local.ecr_repository_arns
  }

  statement {
    sid    = "TaskLogging"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = local.log_group_arns
  }

  statement {
    sid       = "ReadInjectedSecrets"
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.secret_arn_prefix]
  }

  # kms:Decrypt is pinned to Secrets-Manager-mediated calls so the role cannot
  # use the CMK to decrypt other CMK-encrypted material (S3, logs).
  # NOTE: when ECR (global stack) or the ECS log group adopts CMK encryption in
  # AF-013, add matching kms:Decrypt/GenerateDataKey statements via ecr/logs.
  statement {
    sid       = "DecryptSecretsCmk"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [var.kms_key_arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${data.aws_region.current.name}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${var.name_prefix}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-task-execution"
  })
}

resource "aws_iam_role_policy" "task_execution" {
  name   = "${var.name_prefix}-task-execution"
  role   = aws_iam_role.task_execution.id
  policy = data.aws_iam_policy_document.execution.json
}

# --- Per-service task roles (the application's own identity) ----------------

resource "aws_iam_role" "task" {
  for_each = toset(var.services)

  name               = "${var.name_prefix}-${each.value}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.value}-task"
  })
}

# Attach an inline app policy only for services that were given one.
resource "aws_iam_role_policy" "task" {
  for_each = { for svc, policy in var.task_role_policies : svc => policy if contains(var.services, svc) }

  name   = "${var.name_prefix}-${each.key}-task"
  role   = aws_iam_role.task[each.key].id
  policy = each.value
}
