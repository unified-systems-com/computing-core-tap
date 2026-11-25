"""Generic facts about a container image, and the image tag type (req-computing-core-image-facts-*, req-computing-core-image-tag-*)."""

import json
import uuid
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration
from tap_plugin.computing_core.image_reference import canonical_repository

from tap_grid.constraints import InvalidEdgeError
from tap_grid.grift import grift_import
from tap_grid.grift.upgrade import build_header
from tap_grid.models import Entity
from tap_grid.registry import get_model_class
from tap_grid.services import create_edge, delete_node
from tap_plugin.computing_core.key_dimensions import HOST_TYPE_ENTRY
from tap_plugin.computing_core.tests.conftest import create_node

PLUGIN = Path(__file__).resolve().parents[1]
HOST, TAG = "computing_core__host", "computing_core__image_tag"
DIGEST, OTHER = "sha256:" + "a" * 64, "sha256:" + "b" * 64
IMAGE = {"host_type": "oci-digest", "stable_id": DIGEST, "kind": "container", "name": "ghcr.io/org/app:1.2"}
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
        assert get_model_class(HOST).NATURAL_KEY == (HOST_TYPE_ENTRY, "stable_id")

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
            model(**{k: v for k, v in IMAGE.items() if k != "host_type"}, image_built_at=datetime(2026, 11, 1, 8)).validate_image_built_at()  # noqa: DTZ001 - the naive value is the case under test
        model(**{k: v for k, v in IMAGE.items() if k != "host_type"}, image_built_at=datetime(2026, 11, 1, 8, tzinfo=UTC)).validate_image_built_at()

    def test_a_machine_host_may_state_its_architecture(self):
        host = _create(HOST, {"host_type": "assert", "stable_id": "build-box", "kind": "server", "architecture": "arm64"})
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
    def test_every_key_part_is_required(self, missing):
        assert not create_node(TAG, {k: v for k, v in NAME.items() if k != missing}).success

    @pytest.mark.parametrize("empty", ["repository", "tag"])
    def test_repository_and_tag_are_not_empty(self, empty):
        # An empty registry is a reference that named none: Docker Hub (req-computing-core-image-tag-6).
        assert not create_node(TAG, {**NAME, empty: ""}).success

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


#: (registry, repository) as a writer may send them -> Docker's canonical form (req-computing-core-image-tag-6).
CANONICAL = [
    # No registry host: Docker Hub, and a one-component name is an official image under library/.
    (("", "nginx"), ("docker.io", "library/nginx")),
    (("", "myorg/app"), ("docker.io", "myorg/app")),
    (("", "a/b/c"), ("docker.io", "a/b/c")),
    (("docker.io", "nginx"), ("docker.io", "library/nginx")),
    # Docker Hub's other names.
    (("index.docker.io", "nginx"), ("docker.io", "library/nginx")),
    (("index.docker.io", "myorg/app"), ("docker.io", "myorg/app")),
    (("registry-1.docker.io", "nginx"), ("docker.io", "library/nginx")),
    (("registry-1.docker.io", "library/nginx"), ("docker.io", "library/nginx")),
    # The first component is a host only with a "." or ":", as localhost, or upper-case.
    (("", "ghcr.io/org/app"), ("ghcr.io", "org/app")),
    (("", "registry.example:5000/app"), ("registry.example:5000", "app")),
    (("", "localhost/app"), ("localhost", "app")),
    (("", "Registry/app"), ("Registry", "app")),
    (("myorg", "app"), ("docker.io", "myorg/app")),
    # library/ is Docker Hub's alone: a one-component repository elsewhere stays as it is.
    (("localhost:5000", "app"), ("localhost:5000", "app")),
    (("localhost", "app"), ("localhost", "app")),
    (("registry.example:5000", "app"), ("registry.example:5000", "app")),
    # Already canonical.
    (("docker.io", "library/nginx"), ("docker.io", "library/nginx")),
    (("docker.io", "myorg/app"), ("docker.io", "myorg/app")),
    (("ghcr.io", "org/app"), ("ghcr.io", "org/app")),
    # No repository is no name: left for validation to refuse.
    (("", ""), ("", "")),
]


class TestCanonicalRepository:
    @pytest.mark.parametrize(("given", "canonical"), CANONICAL)
    def test_docker_s_rule(self, given, canonical):
        assert canonical_repository(*given) == canonical

    @pytest.mark.parametrize(("given", "canonical"), CANONICAL)
    def test_the_canonical_form_is_a_fixed_point(self, given, canonical):
        assert canonical_repository(*canonical) == canonical


def _tag_rows():
    return list(get_model_class(TAG).objects.values_list("registry", "repository", "tag"))


@pytest.mark.django_db
class TestDockerHubTagsJoin:
    def test_a_short_reference_is_stored_in_canonical_form_and_named_by_it(self):
        tag = _create(TAG, {"registry": "", "repository": "nginx", "tag": "1.25"})
        assert (tag.registry, tag.repository, tag.tag) == ("docker.io", "library/nginx", "1.25")
        assert Entity.objects.get(pk=tag.entity_id).name == "docker.io/library/nginx:1.25"

    def test_a_user_repository_gains_only_the_registry(self):
        tag = _create(TAG, {"registry": "", "repository": "myorg/app", "tag": "2"})
        assert tag.get_name() == "docker.io/myorg/app:2"

    def test_the_tag_is_kept_as_written(self):
        tag = _create(TAG, {"registry": "", "repository": "nginx", "tag": "1.25-Alpine"})
        assert tag.tag == "1.25-Alpine"

    def test_another_registry_is_left_as_it_is(self):
        tag = _create(TAG, {"registry": "localhost:5000", "repository": "app", "tag": "1"})
        assert (tag.registry, tag.repository) == ("localhost:5000", "app")

    @pytest.mark.parametrize(
        "spelling",
        [
            ("", "nginx"),
            ("docker.io", "nginx"),
            ("index.docker.io", "nginx"),
            ("registry-1.docker.io", "library/nginx"),
        ],
    )
    def test_every_spelling_finds_the_canonical_row(self, spelling):
        row = _create(TAG, {"registry": "docker.io", "repository": "library/nginx", "tag": "1.25"})
        found = get_model_class(TAG).find_existing(registry=spelling[0], repository=spelling[1], tag="1.25")
        assert found is not None and found.entity_id == row.entity_id

    def test_a_short_spelling_does_not_find_another_tag(self):
        _create(TAG, {"registry": "docker.io", "repository": "library/nginx", "tag": "1.25"})
        assert get_model_class(TAG).find_existing(registry="", repository="nginx", tag="1.26") is None
        assert get_model_class(TAG).find_existing(registry="localhost:5000", repository="nginx", tag="1.25") is None

    def test_a_canonical_part_that_no_longer_fits_its_column_is_refused(self):
        assert not create_node(TAG, {"registry": "", "repository": "n" * 250, "tag": "1"}).success

    def test_two_writers_spellings_import_as_one_tag(self):
        # ECS writes the reference as the task definition spelled it; Anchore writes Docker's expanded form.
        for registry, repository in [("", "nginx"), ("docker.io", "library/nginx"), ("index.docker.io", "nginx")]:
            result = grift_import(_tag_batch(registry, repository, name=f"{repository}:1.25"))
            assert result.success, [e.message for e in result.errors[:5]]
        assert _tag_rows() == [("docker.io", "library/nginx", "1.25")]


def _tag_batch(registry: str, repository: str, name: str = "docker.io/library/nginx:1.25") -> dict:
    """A GRIFT document carrying one image tag, keyed by its natural key (no entity id)."""
    node = {
        "entity": {"ref": "tag", "entity_type": TAG, "name": name, "dimensions": {"tap.computing": "runtime"}},
        "node": {"registry": registry, "repository": repository, "tag": "1.25"},
    }
    document: dict = {
        "_reserved": {},
        "batches": [
            {
                "batch_entity": {"entity_id": str(uuid.uuid4()), "entity_type": "batch", "name": "image tag test", "dimensions": {}},
                "batch_node": {"name": "image tag test", "description": "", "source": "test", "metadata": {}},
                "nodes": [node],
                "edges": [],
            }
        ],
    }
    document["metadata"] = build_header(document)
    return document


@pytest.mark.django_db
class TestImageTagReobservation:
    """The rule is core's natural-key hook (computing-core-tap#93), so a write is compared in canonical form.

    Core skips a write that changes nothing (tap req-grid-history-reobservation), deciding before ``save``.
    The canonical spelling has to be in place by then, or a writer's short spelling would read as a change
    on every pass: a history row and a version each time with nothing different.
    """

    def _only_row(self):
        model = get_model_class(TAG)
        rows = list(model.objects.all())
        assert [(r.registry, r.repository, r.tag) for r in rows] == [("docker.io", "library/nginx", "1.25")]
        return model, rows[0]

    @pytest.mark.parametrize(
        "spellings",
        [
            [("docker.io", "library/nginx"), ("", "nginx"), ("", "nginx")],
            [("", "nginx"), ("docker.io", "library/nginx"), ("", "nginx")],
            [("", "nginx"), ("index.docker.io", "nginx"), ("registry-1.docker.io", "library/nginx")],
        ],
    )
    def test_a_reimport_in_either_spelling_is_one_row_one_history_row_version_1(self, spellings):
        for registry, repository in spellings:
            result = grift_import(_tag_batch(registry, repository))
            assert result.success, [e.message for e in result.errors[:5]]
        model, row = self._only_row()
        assert model.history.filter(entity_id=row.entity_id).count() == 1
        assert Entity.objects.get(pk=row.entity_id).version == 1

    @pytest.mark.parametrize("spelling", [("", "nginx"), ("docker.io", "nginx"), ("docker.io", "library/nginx")])
    def test_the_lookup_resolves_either_spelling(self, spelling, default_caller_context):
        from tap_grid.services import find_by_natural_key

        assert grift_import(_tag_batch("", "nginx")).success
        model, row = self._only_row()
        key = {"registry": spelling[0], "repository": spelling[1], "tag": "1.25"}
        assert find_by_natural_key(TAG, key, caller_context=default_caller_context) == row.entity_id
        assert model.find_existing(**key).entity_id == row.entity_id

    def test_the_rule_is_core_s_hook_and_leaves_other_entries_alone(self):
        model = get_model_class(TAG)
        assert model.normalize_natural_key({"registry": "", "repository": "nginx", "tag": "1.25"}) == {
            "registry": "docker.io",
            "repository": "library/nginx",
            "tag": "1.25",
        }
        # A hole stays a hole, for the lookup to answer "not found".
        hole = {"registry": None, "repository": "nginx", "tag": "1.25"}
        assert model.normalize_natural_key(dict(hole)) == hole
        # Idempotent, as core requires: the canonical key is a fixed point.
        canonical = {"registry": "docker.io", "repository": "library/nginx", "tag": "1.25"}
        assert model.normalize_natural_key(dict(canonical)) == canonical
        # No save, full_validate or find_existing override is left to restate the rule.
        assert not {"save", "full_validate", "find_existing"} & set(vars(model))
