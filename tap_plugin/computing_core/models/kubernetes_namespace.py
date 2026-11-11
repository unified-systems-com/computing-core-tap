"""Kubernetes Namespace — a namespace object, identified by the uid Kubernetes assigned."""

from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models

from tap_grid.models import BaseModel

#: A Kubernetes label map: string keys to string values. Null is unobserved.
LABELS_SCHEMA: dict[str, Any] = {"type": ["object", "null"], "additionalProperties": {"type": "string"}}

#: Annotation keys that hold a whole applied object, and so whatever secret values were written into
#: it. ``kubectl apply`` records the object it applied under the first. They are never stored: a
#: write that carries one is refused, so a producer must leave them out.
MANIFEST_ANNOTATION_KEYS: frozenset[str] = frozenset({"kubectl.kubernetes.io/last-applied-configuration"})


def annotations_field(what: str) -> models.JSONField:
    """The ``annotations`` field of a Kubernetes object type, the same on each type that has one."""
    return models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text=(
            f"metadata.annotations as reported, less the keys this plugin refuses. Null = not observed; {{}} = the {what} has none. "
            "A key that holds a whole applied manifest (kubectl.kubernetes.io/last-applied-configuration) is refused on write, "
            "because it can carry secret values (req-computing-core-kubernetes-10)."
        ),
    )


def refuse_manifest_annotations(annotations: Any) -> None:
    """Raise when an annotation map carries a key that holds a whole applied manifest."""
    if isinstance(annotations, dict):
        refused = sorted(MANIFEST_ANNOTATION_KEYS & set(annotations))
        if refused:
            raise ValidationError({"annotations": [f"the annotation {refused[0]} holds a whole applied manifest and is never stored; leave it out."]})


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
    name = models.CharField(max_length=255, blank=True, default="", help_text="metadata.name (default, kube-system).")
    labels = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text="metadata.labels as reported. Null = not observed; {} = the namespace has no labels.",
    )
    annotations = annotations_field("namespace")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__kubernetes_namespace"

    def validate(self) -> None:
        """No annotation key that carries a whole applied manifest is stored (req-computing-core-kubernetes-10)."""
        refuse_manifest_annotations(self.annotations)

    def get_name(self) -> str:
        return self.name or self.uid

    def __str__(self) -> str:
        return self.get_name()
