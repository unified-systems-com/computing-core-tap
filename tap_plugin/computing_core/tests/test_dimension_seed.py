"""The dimension seed (req-computing-core-dimensions-4, -5, -6).

Dimension nodes are declared before anything stamps them, never minted on demand (George
2026-11-12, aws-build Q50): a key with no node is how a grid fills with misspelled dimensions.
So every key this plugin stamps, and the two scope dimensions its keyed types will use, must be
in the seed with a fixed id.
"""

import json
import uuid
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration

from tap_grid.grift import grift_import
from tap_grid.models import Dimension

SEED = Path(__file__).resolve().parent.parent / "grift" / "dimension.grift.json"
EXPECTED = {
    "tap.computing": "019dd143-3e8f-73e4-b0fa-e69fcf3ab3ac",
    "tap.web": "019e73e6-6da5-7377-8771-677adb59bc0a",
    "tap.computing.network_name": "01a1d108-d78a-71af-ac0d-4412bd3c7ed3",
    "tap.computing.host": "01a1d108-d78a-71af-ac0d-44131c0156fc",
}


def _seed() -> dict:
    return json.loads(SEED.read_text(encoding="utf-8"))


def _nodes() -> list[dict]:
    return [node for batch in _seed()["batches"] for node in batch["nodes"]]


class TestTheSeedDocument:
    def test_it_names_each_dimension_with_its_fixed_id(self) -> None:
        declared = {node["node"]["name"]: node["entity"]["entity_id"] for node in _nodes()}
        assert declared == EXPECTED

    def test_ids_are_uuids_and_names_agree(self) -> None:
        for node in _nodes():
            assert node["entity"]["entity_type"] == "dimension"
            assert node["entity"]["name"] == node["node"]["name"]
            assert node["node"]["description"].strip()
            uuid.UUID(node["entity"]["entity_id"])

    def test_every_key_the_plugin_stamps_has_a_node(self) -> None:
        """Each DEFAULT_DIMENSIONS key on a computing_core model is declared in the seed."""
        from django.apps import apps

        stamped = set()
        for model in apps.get_app_config("computing_core").get_models():
            stamped |= set(getattr(model, "DEFAULT_DIMENSIONS", {}) or {})
        declared = {node["node"]["name"] for node in _nodes()}
        assert stamped, "no computing_core model declares DEFAULT_DIMENSIONS"
        assert stamped <= declared, f"stamped but undeclared: {sorted(stamped - declared)}"


@pytest.mark.django_db
class TestTheSeedImports:
    def test_the_seed_lands_every_node(self) -> None:
        result = grift_import(_seed())
        assert result.success, result
        for name, entity_id in EXPECTED.items():
            node = Dimension.objects.get(entity_id=entity_id)
            assert node.name == name

    def test_reimporting_the_seed_is_idempotent(self) -> None:
        assert grift_import(_seed()).success
        assert grift_import(_seed()).success
        assert Dimension.objects.filter(entity_id__in=list(EXPECTED.values())).count() == len(EXPECTED)
