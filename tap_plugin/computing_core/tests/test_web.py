"""Domain-specific tests for the web-native Computing Core types.

`web_host` and `web_document` (req-computing-core-models-6). These cover service-layer
creation, required fields, display projection and the `tap.web` web-native marker
(req-computing-core-web-marker). The `HOSTS_DOCUMENT` / `FETCHES_DOCUMENT` edges were retired
on 2026-10-02 (computing-core#25); the last class checks they stay retired.
"""

import importlib
import tomllib
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration

from tap_grid.models import Entity
from tap_grid.registry import get_model_class
from tap_grid.services import create_edge, create_node


def _create(type_slug: str, payload: dict):
    """Create a node via the service layer and return the typed domain object."""
    result = create_node(type_slug, payload)
    assert result.success, f"create_node failed: {result.errors}"
    entity = Entity.objects.get(pk=result.entity_id)
    model_cls = get_model_class(type_slug)
    return model_cls.objects.get(entity=entity)


@pytest.mark.django_db
class TestWebHost:
    def test_create_and_display(self):
        node = _create("computing_core__web_host", {"name": "CISA", "hostname": "www.cisa.gov"})
        node.entity.refresh_from_db()
        assert node.hostname == "www.cisa.gov"
        assert node.entity.name == "CISA"

    def test_name_falls_back_to_hostname(self):
        node = _create("computing_core__web_host", {"hostname": "www.cisa.gov"})
        node.entity.refresh_from_db()
        assert node.entity.name == "www.cisa.gov"

    def test_hostname_required(self):
        result = create_node("computing_core__web_host", {"name": "no host"})
        assert not result.success

    def test_web_native_marker(self):
        node = _create("computing_core__web_host", {"hostname": "www.cisa.gov"})
        assert node.entity.dimensions.get("tap.computing") == "network"
        assert node.entity.dimensions.get("tap.web") == "native"


@pytest.mark.django_db
class TestWebDocument:
    def test_create_with_metadata(self):
        node = _create(
            "computing_core__web_document",
            {
                "name": "CISA KEV catalog",
                "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
                "content_type": "application/json",
                "version": "2026.05.29",
                "retrieved_at": "2026-05-29T12:00:00Z",
            },
        )
        assert node.content_type == "application/json"
        assert node.version == "2026.05.29"
        assert node.retrieved_at is not None

    def test_url_required(self):
        result = create_node("computing_core__web_document", {"name": "no url"})
        assert not result.success

    def test_web_native_marker(self):
        node = _create("computing_core__web_document", {"url": "https://example.com/doc.json"})
        assert node.entity.dimensions.get("tap.computing") == "storage"
        assert node.entity.dimensions.get("tap.web") == "native"


_RETIRED = ("FETCHES_DOCUMENT__computing_core", "HOSTS_DOCUMENT__computing_core")
_PLUGIN_DIR = Path(__file__).resolve().parents[1]


class TestRetiredDocumentEdges:
    def test_the_manifest_defines_neither(self):
        edges = tomllib.loads((_PLUGIN_DIR / "tap-plugin.toml").read_text())["edges"]
        assert not set(_RETIRED) & set(edges)
        assert "GENERATES_FILE__computing_core" in edges, "positive control: the manifest's edges were read"
        for slug in _RETIRED:
            assert not (_PLUGIN_DIR / "edges" / f"{slug.split('__')[0]}.edge.json").exists()

    @pytest.mark.django_db
    def test_the_migration_deletes_retired_rows_and_keeps_the_rest(self):
        from django.apps import apps

        from tap_grid.models import Edge

        migration = importlib.import_module("tap_plugin.computing_core.migrations.0005_retire_document_edge_types")
        assert set(migration._RETIRED_EDGE_TYPES) == set(_RETIRED)

        host = _create("computing_core__web_host", {"hostname": "www.cisa.gov"})
        doc = _create("computing_core__web_document", {"url": "https://www.cisa.gov/feed.json"})
        file = _create("computing_core__file", {"file_path": "/tmp/fetcher"})
        retired = [
            create_edge(host.entity, doc.entity, "HOSTS_DOCUMENT__computing_core"),
            create_edge(file.entity, doc.entity, "FETCHES_DOCUMENT__computing_core"),
        ]
        kept = create_edge(file.entity, doc.entity, "GENERATES_FILE__computing_core")

        migration.delete_retired_edges(apps, None)

        assert not Edge.objects.filter(pk__in=[e.pk for e in retired]).exists()
        assert not Entity.objects.filter(pk__in=[e.entity_id for e in retired]).exists()
        assert Edge.objects.filter(pk=kept.pk).exists()
        assert Entity.objects.filter(pk__in=[host.entity_id, doc.entity_id, file.entity_id]).count() == 3
