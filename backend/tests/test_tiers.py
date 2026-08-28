from __future__ import annotations

from pathlib import Path

from app.api.main import public_tier, tier_for_user
from app.storage import db


def test_tier_selection_is_isolated_per_user(isolated_storage: Path) -> None:
    user_a = db.create_user("A", "Alpha", "tier-a@example.test", "700000101", "hash")
    user_b = db.create_user("B", "Beta", "tier-b@example.test", "700000102", "hash")

    db.set_user_tier(user_a["id"], "assane_eleve")

    assert tier_for_user(user_a["id"]).id == "assane_eleve"
    assert tier_for_user(user_b["id"]).id == "assane_moyen"
    assert public_tier(tier_for_user(user_a["id"]))["image_generation_enabled"] is True


def test_tier_policy_exposes_no_provider_secrets(isolated_storage: Path) -> None:
    user = db.create_user("A", "Alpha", "tier-c@example.test", "700000103", "hash")
    policy = public_tier(tier_for_user(user["id"]))

    assert "api_key" not in policy
    assert "password" not in policy
    assert policy["name"] == "Assane Moyen"
    assert policy["deployment_targets"] == ["vercel"]
