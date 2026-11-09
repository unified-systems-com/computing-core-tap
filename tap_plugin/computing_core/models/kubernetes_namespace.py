"""Kubernetes Namespace — a namespace object, identified by the uid Kubernetes assigned."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel

#: A Kubernetes label map: string keys to string values. Null is unobserved.
LABELS_SCHEMA: dict[str, Any] = {"type": ["object", "null"], "additionalProperties": {"type": "string"}}


class KubernetesNamespace(BaseModel):
    """One Namespace object in a Kubernetes cluster.

    Identity is the ``metadata.uid`` Kubernetes assigned. A uid is distinct over the whole life
    of its cluster, and a namespace deleted and created again under the same name gets a new
    one, so the name is not identity. The cluster is deliberately not part of the key: a cluster
    first identified by an operator's name and later by its kube-system uid would otherwise
    re-key every namespace in it. Which cluster a namespace is in is the ``CONTAINS_NAMESPACE``
    edge.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-kubernetes).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__kubernetes_namespace"
    ENTITY_NAME: ClassVar[str] = "Kubernetes Namespace"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "One Namespace object in a Kubernetes cluster, identified by the uid the cluster assigned it."
    )
    ENTITY_ICON: ClassVar[str] = "kubernetes-namespace"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "runtime"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("uid",)
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#5B8DEF", "border": "#1A3F8F", "label": "#FFFFFF"},
        }
    }

    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "computing_core__kubernetes_pod"}], "edges": [{"type": "CONTAINS_POD__computing_core"}]},
    ]
    # Declared so the grid refuses any other inbound edge: a type that declares nothing is unconstrained.
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {
            "nodes": [{"type": "computing_core__kubernetes_cluster"}],
            "edges": [{"type": "CONTAINS_NAMESPACE__computing_core"}],
        },
    ]
    # A pod exists only in its namespace.
    CONTAINMENT_EDGES: ClassVar[tuple[str, ...]] = ("CONTAINS_POD__computing_core",)

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "uid": {"type": "string", "minLength": 1},
        "name": {"type": "string"},
        "labels": LABELS_SCHEMA,
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "uid": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "labels": {"validation": "jsonschema", "schema": LABELS_SCHEMA},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["uid"]

    uid = models.CharField(
        max_length=64, blank=True, default="", help_text="metadata.uid as the cluster assigned it. Identity."
    )
    name = models.CharField(max_length=255, blank=True, default="", help_text="metadata.name (default, kube-system).")
    labels = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text="metadata.labels as reported. Null = not observed; {} = the namespace has no labels.",
    )

    class Meta(BaseModel.Meta):
        db_table = "computing_core__kubernetes_namespace"

    def get_name(self) -> str:
        return self.name or self.uid

    def __str__(self) -> str:
        return self.get_name()
