"""Kubernetes Cluster — one cluster, named by the authority that identified it."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class KubernetesCluster(BaseModel):
    """One Kubernetes cluster.

    Kubernetes gives a cluster no identifier of its own, so identity is ``(realm, stable_id)``,
    the pattern ``host`` uses: the realm names whose numbering ``stable_id`` comes from. Two
    realms are in use. ``kube-system-uid`` is the uid of the cluster's ``kube-system`` namespace,
    the identifier a reader of the cluster's API can always derive. ``assert`` is the name an
    operator gave the cluster, used when that uid was not observed. One cluster seen through
    both is two nodes; joining them is a separate assertion and is never inferred.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-kubernetes).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__kubernetes_cluster"
    ENTITY_NAME: ClassVar[str] = "Kubernetes Cluster"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "One Kubernetes cluster, identified by the uid of its kube-system namespace where that is "
        "known and by an operator's name for it otherwise."
    )
    ENTITY_ICON: ClassVar[str] = "kubernetes-cluster"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "runtime"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("realm", "stable_id")
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#326CE5", "border": "#1A3F8F", "label": "#FFFFFF"},
        }
    }

    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {
            "nodes": [{"type": "computing_core__kubernetes_namespace"}],
            "edges": [{"type": "CONTAINS_NAMESPACE__computing_core"}],
        },
        {
            "nodes": [{"type": "computing_core__kubernetes_node"}],
            "edges": [{"type": "REGISTERS_NODE__computing_core"}],
        },
    ]
    # A namespace and a Node object exist only in their cluster. The machine behind a node is a
    # host, reached from the node by a reference, so it stays live when the cluster retires.
    CONTAINMENT_EDGES: ClassVar[tuple[str, ...]] = (
        "CONTAINS_NAMESPACE__computing_core",
        "REGISTERS_NODE__computing_core",
    )

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "realm": {"type": "string", "minLength": 1},
        "stable_id": {"type": "string", "minLength": 1},
        "name": {"type": "string"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "realm": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "stable_id": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["realm", "stable_id"]

    realm = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="The authority that issued stable_id: kube-system-uid, or assert for an operator's own name.",
    )
    stable_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The cluster's identifier within realm: the kube-system namespace uid, or the operator's name.",
    )
    name = models.CharField(max_length=255, blank=True, default="", help_text="Display name of the cluster.")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__kubernetes_cluster"

    def get_name(self) -> str:
        return self.name or self.stable_id

    def __str__(self) -> str:
        return self.get_name()
