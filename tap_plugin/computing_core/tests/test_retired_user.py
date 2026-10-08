"""`computing_core__user` stays retired (computing-core#27).

A person is `identity_core__human`; an account on a host is `os_user`. These check the manifest
no longer defines `user`, core's retired-type registry knows why, an older seed that still
carries a `user` node is stripped rather than failed, and migration 0007 removes the rows a
grid upgraded in place still holds.
"""

import importlib
import tomllib
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration

from tap_grid.grift.retired import strip_retired_types
from tap_grid.models import Edge, Entity
from tap_grid.registry import get_model_class, retired_entity_reason
from tap_grid.services import create_edge, create_node
from tap_grid.write_guard import unguarded_write

RETIRED = "computing_core__user"
_PLUGIN_DIR = Path(__file__).resolve().parents[1]


def test_the_manifest_no_longer_defines_user():
    models = tomllib.loads((_PLUGIN_DIR / "tap-plugin.toml").read_text())["models"]
    assert RETIRED not in models
    assert "computing_core__os_user" in models, "positive control: the manifest's models were read"
    assert not (_PLUGIN_DIR / "models" / "user.py").exists()


def test_core_records_the_retirement_and_its_reason():
    reason = retired_entity_reason(RETIRED)
    assert reason and "identity_core__human" in reason
    with pytest.raises(LookupError):
        get_model_class(RETIRED)


@pytest.mark.django_db
def test_an_older_seed_carrying_user_is_stripped_not_failed():
    user_id = "019e73fe-33af-72c4-b998-1b6bc5ec7e91"
    doc = {
        "metadata": {"grift_version": "0"},
        "batches": [
            {
                "batch_entity": {"entity_id": "019e73fe-33ae-7375-ba2e-17710feab3e5", "entity_type": "batch"},
                "nodes": [
                    {"entity": {"entity_id": user_id, "entity_type": RETIRED, "name": "Sam"}, "node": {"name": "Sam"}},
                ],
                "edges": [],
            }
        ],
    }
    stripped_doc, report = strip_retired_types(doc)
    assert report.nodes == ((RETIRED, user_id),)
    assert stripped_doc["batches"][0]["nodes"] == []


@pytest.mark.django_db
def test_the_migration_deletes_user_rows_and_their_edges_and_keeps_the_rest():
    from django.apps import apps

    migration = importlib.import_module("tap_plugin.computing_core.migrations.0007_retire_user_rows")
    assert migration.RETIRED_ENTITY_TYPE == RETIRED

    # A grid upgraded in place: a user spine row (its typed table is gone by the time this
    # suite runs, which is the state the migration leaves) with an edge in and an edge out.
    with unguarded_write():
        user = Entity.objects.create(entity_type=RETIRED, name="Sam")
    result = create_node("computing_core__file", {"file_path": "/etc/passwd"})
    assert result.success, result.errors
    file = Entity.objects.get(pk=result.entity_id)
    other = Entity.objects.get(pk=create_node("computing_core__program", {"program_name": "sshd"}).entity_id)
    retired_edges = [
        create_edge(user, file, "GENERATES_FILE__computing_core"),
        create_edge(other, user, "GENERATES_FILE__computing_core"),
    ]
    kept = create_edge(other, file, "GENERATES_FILE__computing_core")

    migration.delete_user_rows(apps, None)

    assert not Entity.objects.filter(pk=user.pk).exists()
    assert not Edge.objects.filter(pk__in=[e.pk for e in retired_edges]).exists()
    assert not Entity.objects.filter(pk__in=[e.entity_id for e in retired_edges]).exists()
    assert Edge.objects.filter(pk=kept.pk).exists()
    assert Entity.objects.filter(pk__in=[file.pk, other.pk]).count() == 2
