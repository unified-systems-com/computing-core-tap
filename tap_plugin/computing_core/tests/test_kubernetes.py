"""Kubernetes runtime placement: five types and six edges (req-computing-core-kubernetes-*)."""

import json
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration

from tap_grid.constraints import InvalidEdgeError
from tap_grid.models import Entity
from tap_grid.registry import get_model_class
from tap_grid.services import create_edge, create_node, delete_node, replace_node

PLUGIN = Path(__file__).resolve().parents[1]
CLUSTER = "computing_core__kubernetes_cluster"
NAMESPACE = "computing_core__kubernetes_namespace"
POD = "computing_core__kubernetes_pod"
NODE = "computing_core__kubernetes_node"
CONTAINER = "computing_core__kubernetes_container"
HOST = "computing_core__host"
TYPES = (CLUSTER, NAMESPACE, POD, NODE, CONTAINER)
EDGES = (
    "CONTAINS_NAMESPACE",
    "CONTAINS_POD",
    "RUNS_CONTAINER",
    "REGISTERS_NODE",
    "SCHEDULED_ON_NODE",
    "BACKED_BY_HOST",
)
DIGEST = "sha256:" + "a" * 64


def _create(type_slug: str, payload: dict):
    result = create_node(type_slug, payload)
    assert result.success, f"create_node failed: {result.errors}"
    return get_model_class(type_slug).objects.get(entity=Entity.objects.get(pk=result.entity_id))


def _edge(source, target, slug: str):
    return create_edge(source.entity, target.entity, f"{slug}__computing_core")


def _live(node) -> bool:
    return Entity.objects.get(pk=node.entity_id).deleted_at is None


@pytest.fixture
def chain(db):
    """One cluster with a namespace, a node backed by a host, and a pod running one container."""
    cluster = _create(CLUSTER, {"realm": "kube-system-uid", "stable_id": "c-uid-1", "name": "prod"})
    namespace = _create(NAMESPACE, {"uid": "ns-uid-1", "name": "default", "labels": {}})
    pod = _create(POD, {"uid": "pod-uid-1", "name": "web-0", "labels": {"app": "web"}})
    node = _create(NODE, {"uid": "node-uid-1", "name": "ip-10-0-1-2", "kubelet_version": "v1.31.0"})
    machine = _create(HOST, {"realm": "kubernetes-node-uid", "stable_id": "node-uid-1", "name": "ip-10-0-1-2"})
    container = _create(CONTAINER, {"pod_uid": "pod-uid-1", "name": "web", "image_reference": "ghcr.io/o/web:1"})
    image = _create(HOST, {"realm": "oci-digest", "stable_id": DIGEST, "kind": "container"})
    _edge(cluster, namespace, "CONTAINS_NAMESPACE")
    _edge(namespace, pod, "CONTAINS_POD")
    _edge(pod, container, "RUNS_CONTAINER")
    _edge(cluster, node, "REGISTERS_NODE")
    _edge(pod, node, "SCHEDULED_ON_NODE")
    _edge(node, machine, "BACKED_BY_HOST")
    create_edge(container.entity, image.entity, "RUNS_IMAGE__computing_core")
    return {
        "cluster": cluster,
        "namespace": namespace,
        "pod": pod,
        "node": node,
        "machine": machine,
        "container": container,
        "image": image,
    }


@pytest.mark.django_db
class TestTypes:
    @pytest.mark.parametrize("type_slug", TYPES)
    def test_dimension_icon_and_declared_key(self, type_slug):
        model = get_model_class(type_slug)
        assert model.DEFAULT_DIMENSIONS == {"tap.computing": "runtime"}
        svg = (PLUGIN / "static" / "computing_core" / "icons" / f"{model.ENTITY_ICON}.svg").read_text()
        assert 'viewBox="0 0 80 80"' in svg
        assert set(model.FIELD_CRUD_SCHEMA) == set(model.FIELD_VALIDATION_SCHEMA)
        assert "annotations" not in model.FIELD_CRUD_SCHEMA

    def test_natural_keys(self):
        assert get_model_class(CLUSTER).NATURAL_KEY == ("realm", "stable_id")
        assert get_model_class(NAMESPACE).NATURAL_KEY == ("uid",)
        assert get_model_class(POD).NATURAL_KEY == ("uid",)
        assert get_model_class(NODE).NATURAL_KEY == ("uid",)
        assert get_model_class(CONTAINER).NATURAL_KEY == ("pod_uid", "name")

    def test_display_name_and_fallback(self):
        pod = _create(POD, {"uid": "pod-uid-9", "name": "web-0"})
        pod.entity.refresh_from_db()
        assert pod.entity.name == "web-0"
        assert pod.entity.dimensions.get("tap.computing") == "runtime"
        assert _create(POD, {"uid": "pod-uid-8"}).get_name() == "pod-uid-8"
        assert _create(CLUSTER, {"realm": "assert", "stable_id": "prod-east"}).get_name() == "prod-east"

    @pytest.mark.parametrize(
        ("type_slug", "payload"),
        [
            (CLUSTER, {"realm": "assert"}),
            (CLUSTER, {"stable_id": "x"}),
            (NAMESPACE, {"name": "default"}),
            (POD, {"name": "web-0"}),
            (NODE, {"name": "n1"}),
            (CONTAINER, {"pod_uid": "p"}),
            (CONTAINER, {"name": "web"}),
        ],
    )
    def test_key_fields_are_required(self, type_slug, payload):
        assert not create_node(type_slug, payload).success

    def test_a_cluster_under_two_realms_is_two_nodes(self):
        by_uid = _create(CLUSTER, {"realm": "kube-system-uid", "stable_id": "c-uid-1", "name": "prod"})
        by_name = _create(CLUSTER, {"realm": "assert", "stable_id": "prod", "name": "prod"})
        assert by_uid.entity_id != by_name.entity_id
        model = get_model_class(CLUSTER)
        assert model.find_existing(realm="kube-system-uid", stable_id="c-uid-1").pk == by_uid.pk
        assert model.find_existing(realm="assert", stable_id="prod").pk == by_name.pk

    def test_a_recreated_namespace_is_a_second_node(self):
        first = _create(NAMESPACE, {"uid": "ns-uid-1", "name": "team-a"})
        second = _create(NAMESPACE, {"uid": "ns-uid-2", "name": "team-a"})
        assert first.entity_id != second.entity_id
        assert get_model_class(NAMESPACE).find_existing(uid="ns-uid-2").pk == second.pk

    def test_one_uid_is_one_node_whichever_cluster_it_is_drawn_under(self):
        """The accepted cost of keying on the uid alone (req-computing-core-kubernetes-3)."""
        east = _create(CLUSTER, {"realm": "assert", "stable_id": "east"})
        west = _create(CLUSTER, {"realm": "assert", "stable_id": "west"})
        namespace = _create(NAMESPACE, {"uid": "ns-uid-1", "name": "default"})
        _edge(east, namespace, "CONTAINS_NAMESPACE")
        _edge(west, namespace, "CONTAINS_NAMESPACE")
        assert get_model_class(NAMESPACE).find_existing(uid="ns-uid-1").pk == namespace.pk

    def test_labels_keep_three_states(self):
        assert _create(POD, {"uid": "p1"}).labels is None
        assert _create(POD, {"uid": "p2", "labels": {}}).labels == {}
        assert _create(POD, {"uid": "p3", "labels": {"app": "web"}}).labels == {"app": "web"}
        assert not create_node(POD, {"uid": "p4", "labels": {"replicas": 3}}).success

    def test_node_versions_are_null_until_observed(self):
        node = _create(NODE, {"uid": "node-uid-1", "name": "n1", "architecture": "arm64"})
        assert node.architecture == "arm64"
        assert node.kernel_version is None
        assert node.kubelet_version is None
        assert "operating_system" not in get_model_class(NODE).FIELD_CRUD_SCHEMA

    def test_a_restart_changes_the_runtime_id_on_one_container(self):
        container = _create(CONTAINER, {"pod_uid": "pod-uid-1", "name": "web", "container_id": "containerd://aaa"})
        result = replace_node(
            container.entity_id, {"pod_uid": "pod-uid-1", "name": "web", "container_id": "containerd://bbb"}
        )
        assert result.success, result.errors
        found = get_model_class(CONTAINER).find_existing(pod_uid="pod-uid-1", name="web")
        assert found.pk == container.pk
        assert found.container_id == "containerd://bbb"

    def test_same_container_name_in_two_pods_is_two_containers(self):
        first = _create(CONTAINER, {"pod_uid": "pod-uid-1", "name": "web"})
        second = _create(CONTAINER, {"pod_uid": "pod-uid-2", "name": "web"})
        assert first.entity_id != second.entity_id
        assert first.container_id is None


@pytest.mark.django_db
class TestEdges:
    @pytest.mark.parametrize("slug", EDGES)
    def test_definitions_declare_identity_and_dimension(self, slug):
        definition = json.loads((PLUGIN / "edges" / f"{slug}.edge.json").read_text())
        assert definition["slug"] == f"{slug}__computing_core"
        assert definition["identity"] == {"discriminators": []}
        assert definition["default_dimensions"] == {"tap.computing": "runtime"}
        assert len(definition["sources"]) == 1
        assert len(definition["targets"]) == 1

    def test_the_chain_connects(self, chain):
        assert all(_live(node) for node in chain.values())

    def test_edges_refuse_the_wrong_ends(self, chain):
        with pytest.raises(InvalidEdgeError):
            _edge(chain["cluster"], chain["pod"], "CONTAINS_NAMESPACE")
        with pytest.raises(InvalidEdgeError):
            _edge(chain["pod"], chain["machine"], "SCHEDULED_ON_NODE")
        with pytest.raises(InvalidEdgeError):
            _edge(chain["namespace"], chain["container"], "RUNS_CONTAINER")

    def test_retiring_a_pod_retires_its_containers_only(self, chain):
        assert delete_node(chain["pod"].entity_id, cascade="contained").success
        assert not _live(chain["pod"])
        assert not _live(chain["container"])
        for kept in ("namespace", "node", "machine", "image", "cluster"):
            assert _live(chain[kept]), kept

    def test_retiring_a_cluster_retires_its_objects_and_keeps_the_hosts(self, chain):
        assert delete_node(chain["cluster"].entity_id, cascade="contained").success
        for gone in ("cluster", "namespace", "pod", "container", "node"):
            assert not _live(chain[gone]), gone
        assert _live(chain["machine"])
        assert _live(chain["image"])
