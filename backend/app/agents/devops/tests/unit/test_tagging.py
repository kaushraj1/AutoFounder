"""Tag-builder tests."""

from uuid import uuid4

from app.agents.devops.utils.tagging import build_tags


def test_build_tags_includes_required_fields() -> None:
    tags = build_tags("tenant-acme", uuid4(), env="staging")
    assert tags["Tenant"] == "tenant-acme"
    assert tags["Pillar"] == "5"
    assert tags["Env"] == "staging"
    assert tags["ManagedBy"] == "DevOpsAgent"


"""Tag-builder tests."""
