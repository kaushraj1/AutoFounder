provider "aws" {
  region = var.aws_region

  # Required platform tags applied to every taggable resource automatically
  # (CLAUDE.md / deployment.md). Resource-level tags add Name/tier on top.
  default_tags {
    tags = local.common_tags
  }
}
