"""Generic facts about a container image, and the image tag type (req-computing-core-image-facts-*, req-computing-core-image-tag-*)."""

import json
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration

from tap_grid.constraints import InvalidEdgeError
from tap_grid.models import Entity
from tap_grid.registry import get_model_class
from tap_grid.services import create_edge, create_node, delete_node

PLUGIN = Path(__file__).resolve().parents[1]
HOST, TAG = "computing_core__host", "computing_core__image_tag"
DIGEST, OTHER = "sha256:" + "a" * 64, "sha256:" + "b" * 64
IMAGE = {"realm": "oci-digest", "stable_id": DIGEST, "kind": "container", "name": "ghcr.io/org/app:1.2"}
NAME = {"registry": "ghcr.io", "repository": "org/app", "tag": "1.2"}


def _create(type_slug: str, payload: dict):
    result = create_node(type_slug, payload)
    assert result.success, f"create_node failed: {result.errors}"
    return get_model_class(type_slug).objects.get(entity=Entity.objects.get(pk=result.entity_id))


def _live(node) -> bool:
    return Entity.objects.get(pk=node.entity_id).deleted_at is None


@pytest.mark.django_db
class TestImageFactsOnTheHost:
    def test_an_image_host_holds_its_architecture_size_layers_and_build_time(self):
        host = _create(HOST, {**IMAGE, "architecture": "amd64", "image_size_bytes": 123456789012, "image_layer_count": 7, "image_built_at": "2026-11-01T08:00:00Z"})
        assert (host.architecture, host.image_size_bytes, host.image_layer_count) == ("amd64", 123456789012, 7)
        assert host.image_built_at.isoformat().startswith("2026-11-01T08:00:00")

    def test_each_is_null_until_observed(self):
        host = _create(HOST, IMAGE)
        assert (host.architecture, host.image_size_bytes, host.image_layer_count, host.image_built_at) == (None, None, None, None)

    def test_they_are_no_part_of_the_hosts_identity(self):
        assert get_model_class(HOST).NATURAL_KEY == ("realm", "stable_id")

    @pytest.mark.parametrize(
        "fields",
        [{"architecture": "x" * 33}, {"architecture": 7}, {"image_size_bytes": -1}, {"image_size_bytes": "big"}, {"image_layer_count": -1}, {"image_layer_count": 2147483648}, {"image_built_at": "20261101"}, {"image_built_at": "2026-11-01T08:00:00"}],
    )
    def test_a_value_out_of_shape_is_refused(self, fields):
        assert not create_node(HOST, {**IMAGE, **fields}).success

    def test_a_build_time_with_no_zone_is_refused_as_a_datetime_too(self):
        from datetime import UTC, datetime

        from django.core.exceptions import ValidationError

        model = get_model_class(HOST)
        # The service takes a build time only as a string; a datetime object is refused there outright.
        assert not create_node(HOST, {**IMAGE, "image_built_at": datetime(2026, 11, 1, 8, tzinfo=UTC)}).success
        # The model's own check, which a direct save reaches, refuses a datetime with no zone and passes one with.
        with pytest.raises(ValidationError):
            model(**IMAGE, image_built_at=datetime(2026, 11, 1, 8)).validate_image_built_at()  # noqa: DTZ001 - the naive value is the case under test
        model(**IMAGE, image_built_at=datetime(2026, 11, 1, 8, tzinfo=UTC)).validate_image_built_at()

    def test_a_machine_host_may_state_its_architecture(self):
        host = _create(HOST, {"realm": "assert", "stable_id": "build-box", "kind": "server", "architecture": "arm64"})
        assert host.architecture == "arm64" and host.image_size_bytes is None


@pytest.mark.django_db
class TestImageTag:
    def test_dimension_icon_key_and_name(self):
        model = get_model_class(TAG)
        assert model.DEFAULT_DIMENSIONS == {"tap.computing": "runtime"} and model.NATURAL_KEY == ("registry", "repository", "tag")
        assert (PLUGIN / "static" / "computing_core" / "icons" / f"{model.ENTITY_ICON}.svg").is_file()
        tag = _create(TAG, NAME)
        assert tag.get_name() == "ghcr.io/org/app:1.2" and Entity.objects.get(pk=tag.entity_id).name == "ghcr.io/org/app:1.2"

    @pytest.mark.parametrize("missing", ["registry", "repository", "tag"])
    def test_every_key_part_is_required_and_not_empty(self, missing):
        assert not create_node(TAG, {k: v for k, v in NAME.items() if k != missing}).success
        assert not create_node(TAG, {**NAME, missing: ""}).success

    @pytest.mark.parametrize("fields", [{"registry": "r" * 256}, {"repository": "p" * 256}, {"tag": "t" * 129}])
    def test_a_part_longer_than_its_column_is_refused(self, fields):
        assert not create_node(TAG, {**NAME, **fields}).success

    def test_the_same_tag_name_in_two_repositories_is_two_tags(self):
        one, two = _create(TAG, NAME), _create(TAG, {**NAME, "repository": "org/other"})
        assert one.entity_id != two.entity_id


@pytest.mark.django_db
class TestTagsImage:
    def test_a_tag_points_at_an_image_host_and_says_when_it_was_seen(self):
        tag, image = _create(TAG, NAME), _create(HOST, IMAGE)
        edge = create_edge(tag.entity, image.entity, "TAGS_IMAGE__computing_core", {"detected_at": "2026-11-10T12:00:00Z"})
        assert edge.properties == {"detected_at": "2026-11-10T12:00:00Z"}
        assert create_edge(_create(TAG, {**NAME, "tag": "latest"}).entity, image.entity, "TAGS_IMAGE__computing_core").properties in ({}, None)

    def test_a_tag_that_moved_keeps_an_edge_to_each_image_it_was_seen_on(self):
        tag, old, new = _create(TAG, NAME), _create(HOST, IMAGE), _create(HOST, {**IMAGE, "stable_id": OTHER})
        create_edge(tag.entity, old.entity, "TAGS_IMAGE__computing_core", {"detected_at": "2026-10-01T00:00:00Z"})
        create_edge(tag.entity, new.entity, "TAGS_IMAGE__computing_core", {"detected_at": "2026-11-10T00:00:00Z"})
        from tap_grid.models import Edge

        assert Edge.objects.filter(edge_type="TAGS_IMAGE__computing_core", from_entity=tag.entity).count() == 2

    def test_the_wrong_ends_and_an_undeclared_property_are_refused(self):
        tag, image = _create(TAG, NAME), _create(HOST, IMAGE)
        with pytest.raises(InvalidEdgeError):
            create_edge(image.entity, tag.entity, "TAGS_IMAGE__computing_core")
        with pytest.raises(Exception):  # noqa: B017, PT011 - the grid's own error type for a property the schema does not declare
            create_edge(tag.entity, image.entity, "TAGS_IMAGE__computing_core", {"current": True})

    def test_retiring_a_tag_leaves_the_image_and_retiring_the_image_leaves_the_tag(self):
        tag, image = _create(TAG, NAME), _create(HOST, IMAGE)
        create_edge(tag.entity, image.entity, "TAGS_IMAGE__computing_core")
        assert delete_node(tag.entity_id, cascade="contained").success and _live(image)
        other_tag, other = _create(TAG, {**NAME, "tag": "2.0"}), _create(HOST, {**IMAGE, "stable_id": OTHER})
        create_edge(other_tag.entity, other.entity, "TAGS_IMAGE__computing_core")
        assert delete_node(other.entity_id, cascade="contained").success and _live(other_tag)

    @pytest.mark.parametrize("when", ["yesterday", "2026-11-10", "2026-11-10T12:00:00", "20261110T120000Z", ""])
    def test_a_detected_at_that_is_not_a_date_time_with_a_zone_is_refused(self, when):
        tag, image = _create(TAG, NAME), _create(HOST, IMAGE)
        with pytest.raises(Exception):  # noqa: B017, PT011 - the grid's own error type for a property that fails its schema
            create_edge(tag.entity, image.entity, "TAGS_IMAGE__computing_core", {"detected_at": when})

    def test_the_edge_definition_declares_its_ends_and_its_one_property(self):
        definition = json.loads((PLUGIN / "edges" / "TAGS_IMAGE.edge.json").read_text(encoding="utf-8"))
        assert (definition["sources"], definition["targets"]) == ([TAG], [HOST])
        assert list(definition["property_schema"]["properties"]) == ["detected_at"] and definition["property_schema"]["additionalProperties"] is False
