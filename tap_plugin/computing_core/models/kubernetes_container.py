"""Kubernetes Container — one named container of one pod."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class KubernetesContainer(BaseModel):
    """One container of a pod, as the pod names it.

    Identity is ``(pod_uid, name)``. Container names are unique within a pod across every
    container type, so the pair names one container for the pod's whole life. The runtime's own
    container id is not identity: it is empty until the container is created and a restart
    issues a new one, so it is stored as a field (``container_id``) and may change on one node.

    The image the container runs is the ``RUNS_IMAGE`` edge to the image host, keyed by digest.
    ``image_reference`` is the reference the container was started from (a tag), kept because
    many tags name one digest and the digest alone does not say which was used.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-kubernetes).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__kubernetes_container"
    ENTITY_NAME: ClassVar[str] = "Kubernetes Container"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "One named container of a Kubernetes pod, identified by the pod's uid and the container's name."
    )
    ENTITY_ICON: ClassVar[str] = "kubernetes-container"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "runtime"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("pod_uid", "name")
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#A9C4F8", "border": "#1A3F8F", "label": "#0B1F4A"},
        }
    }

    # The image is shared by every container started from it: a reference.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "computing_core__host"}], "edges": [{"type": "RUNS_IMAGE__computing_core"}]},
    ]
    # Declared so the grid refuses any other inbound edge: a type that declares nothing is unconstrained.
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {
            "nodes": [{"type": "computing_core__kubernetes_pod"}],
            "edges": [{"type": "RUNS_CONTAINER__computing_core"}],
        },
    ]

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "pod_uid": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "container_id": {"type": ["string", "null"]},
        "image_reference": {"type": ["string", "null"]},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "pod_uid": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "container_id": {"validation": "jsonschema", "schema": {"type": ["string", "null"]}},
        "image_reference": {"validation": "jsonschema", "schema": {"type": ["string", "null"]}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["pod_uid", "name"]

    pod_uid = models.CharField(
        max_length=64, blank=True, default="", help_text="The uid of the pod this container belongs to. Identity."
    )
    name = models.CharField(
        max_length=255, blank=True, default="", help_text="The container's name within its pod. Identity."
    )
    container_id = models.CharField(  # noqa: DJ001  (req-computing-core-kubernetes-7)
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="The runtime's id for the running container (containerd://...). Null = not observed. Not identity.",
    )
    image_reference = models.CharField(  # noqa: DJ001  (req-computing-core-kubernetes-9)
        max_length=2048,
        blank=True,
        null=True,
        default=None,
        help_text="The image reference the container was started from, as reported. Null = not observed.",
    )

    class Meta(BaseModel.Meta):
        db_table = "computing_core__kubernetes_container"

    def get_name(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.get_name()
