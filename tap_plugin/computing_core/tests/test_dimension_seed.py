"""The dimension seed (req-computing-core-dimensions-4 .. -10).

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
    "tap.computing.kubernetes_cluster": "01a1d123-20bd-74a1-b989-38bc18f4ad43",
    "tap.computing.kubernetes_namespace": "01a1d123-20bd-74a1-b989-38bd1ffcd823",
    # aws_core's former tap.cloud node: computing_core owns the cloud dimension and keeps its id (Q56).
    "tap.computing.cloud": "019dd143-3e8f-73e4-b0fa-e62ac923065d",
    # The kind of credential a thing is (George 2026-11-23, aws-build Q146; computing-core#97).
    "tap.computing.credential": "01a208da-cf75-76a8-af79-420c154a440f",
}

CREDENTIAL = "tap.computing.credential"
# Q146b's starting kinds, in the order the seed lists them. A new kind is added here and in the seed together.
CREDENTIAL_KINDS = [
    "access_key",
    "password",
    "ssh_key",
    "certificate",
    "api_key",
    "token",
    "crypto_key",
    "secret_store",
]
# Every computing_core type that is a credential, and its kind (Q146c).
CREDENTIAL_TYPES = {
    "computing_core__private_key": "crypto_key",
    "computing_core__public_key": "crypto_key",
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


def _node(name: str) -> dict:
    (found,) = [node for node in _nodes() if node["node"]["name"] == name]
    return found


class TestTheCredentialDimension:
    """req-computing-core-dimensions-10: one bounded dimension names the kind of credential."""

    def test_it_is_bounded_to_the_ruled_kinds(self) -> None:
        assert _node(CREDENTIAL)["node"]["values"] == CREDENTIAL_KINDS

    def test_it_is_a_label_never_a_key_and_never_empty(self) -> None:
        node = _node(CREDENTIAL)["node"]
        assert not node.get("usable_in_keys", False)
        assert not node.get("empty_is_meaningful", False)

    def test_its_description_says_what_each_kind_covers(self) -> None:
        description = _node(CREDENTIAL)["node"]["description"]
        for kind in CREDENTIAL_KINDS:
            assert kind in description, kind

    def test_exactly_the_key_types_are_credentials(self) -> None:
        """private_key and public_key carry crypto_key beside their storage tag; no other type is tagged."""
        from django.apps import apps

        tagged = {}
        for model in apps.get_app_config("computing_core").get_models():
            defaults = getattr(model, "DEFAULT_DIMENSIONS", {}) or {}
            if CREDENTIAL in defaults:
                tagged[model.ENTITY_TYPE] = defaults[CREDENTIAL]
                assert defaults.get("tap.computing") == "storage", model.ENTITY_TYPE
        assert tagged == CREDENTIAL_TYPES


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

    def test_a_kind_outside_the_list_is_refused(self) -> None:
        from tap_grid.dimension_map import DimensionWriteError, supplied

        assert grift_import(_seed()).success
        assert Dimension.objects.get(entity_id=EXPECTED[CREDENTIAL]).values == CREDENTIAL_KINDS
        supplied({CREDENTIAL: "crypto_key"})
        with pytest.raises(DimensionWriteError):
            supplied({CREDENTIAL: "secret"})

    def test_a_private_key_lands_tagged_crypto_key(self) -> None:
        from tap_grid.services import create_node
        from tap_plugin.computing_core.models.private_key import PrivateKey
        from tap_plugin.computing_core.tests.conftest import dimension_view

        assert grift_import(_seed()).success
        result = create_node("computing_core__private_key", {"name": "deploy", "algorithm": "ed25519"})
        assert result.success, result.errors
        node = PrivateKey.objects.get(entity__pk=result.entity_id)
        shown = dimension_view(node.entity)
        assert shown.get("tap.computing") == "storage"
        assert shown.get(CREDENTIAL) == "crypto_key"
