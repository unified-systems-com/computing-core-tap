"""Kubernetes Pod — a pod object, identified by the uid Kubernetes assigned."""

from typing import Any, ClassVar

from django.db import models
from tap_plugin.computing_core.models.kubernetes_namespace import LABELS_SCHEMA

from tap_grid.models import BaseModel


class KubernetesPod(BaseModel):
    """One Pod object in a Kubernetes cluster.

    Identity is the ``metadata.uid`` Kubernetes assigned. A pod, as its uid defines it, is never
    moved to another node, and a replacement created under the same name has a new uid, so a
    replaced pod is a new node here. Where the pod sits is carried by edges: its namespace
    (``CONTAINS_POD``), the node it was placed on (``SCHEDULED_ON_NODE``, absent until it is
    placed) and its containers (``RUNS_CONTAINER``).

    Spec: specs/spec-computing-core-v0.md (req-computing-core-kubernetes).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__kubernetes_pod"
    ENTITY_NAME: ClassVar[str] = "Kubernetes Pod"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "One Pod object in a Kubernetes cluster, identified by the uid the cluster assigned it."
    )
    ENTITY_ICON: ClassVar[str] = "kubernetes-pod"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "runtime"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("uid",)
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#7FA8F5", "border": "#1A3F8F", "label": "#0B1F4A"},
        }
    }

    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {
            "nodes": [{"type": "computing_core__kubernetes_container"}],
            "edges": [{"type": "RUNS_CONTAINER__computing_core"}],
        },
        {
            "nodes": [{"type": "computing_core__kubernetes_node"}],
            "edges": [{"type": "SCHEDULED_ON_NODE__computing_core"}],
        },
    ]
    # Declared so the grid refuses any other inbound edge: a type that declares nothing is unconstrained.
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {
            "nodes": [{"type": "computing_core__kubernetes_namespace"}],
            "edges": [{"type": "CONTAINS_POD__computing_core"}],
        },
    ]
    # A container exists only as part of its pod. The node a pod was placed on is a reference.
    CONTAINMENT_EDGES: ClassVar[tuple[str, ...]] = ("RUNS_CONTAINER__computing_core",)

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "uid": {"type": "string", "minLength": 1},
        "name": {"type": "string"},
        "labels": LABELS_SCHEMA,
        "annotations": LABELS_SCHEMA,
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "uid": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "labels": {"validation": "jsonschema", "schema": LABELS_SCHEMA},
        "annotations": {"validation": "jsonschema", "schema": LABELS_SCHEMA},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["uid"]

    uid = models.CharField(
        max_length=64, blank=True, default="", help_text="metadata.uid as the cluster assigned it. Identity."
    )
    name = models.CharField(max_length=255, blank=True, default="", help_text="metadata.name.")
    labels = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text="metadata.labels as reported. Null = not observed; {} = the pod has no labels.",
    )
    annotations = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text=(
            "metadata.annotations as reported, less any key its producer excludes. Null = not observed; {} = the pod has none. "
            "Annotations are free-form and can hold whole applied manifests with secret values in them, so a producer leaves those keys out "
            "(req-computing-core-kubernetes-10)."
        ),
    )

    class Meta(BaseModel.Meta):
        db_table = "computing_core__kubernetes_pod"

    def get_name(self) -> str:
        return self.name or self.uid

    def __str__(self) -> str:
        return self.get_name()
