"""Kubernetes Node — a Node object and what the kubelet reports about it."""

from typing import Any, ClassVar

from django.db import models
from tap_plugin.computing_core.models.kubernetes_namespace import LABELS_SCHEMA, annotations_field, refuse_manifest_annotations

from tap_grid.models import BaseModel


class KubernetesNode(BaseModel):
    """One Node object in a Kubernetes cluster: the cluster's record of a machine that runs pods.

    The Node object and the machine are two things. This type is the Kubernetes record: its uid,
    name, labels and the versions the kubelet reports. The machine is a ``host`` under the realm
    ``kubernetes-node-uid``, reached by ``BACKED_BY_HOST``; the operating system belongs on the
    host (``host.os``) and is not repeated here. That keeps ``host`` generic and gives the
    Kubernetes-only facts a home.

    Identity is the ``metadata.uid`` Kubernetes assigned. A node removed and registered again
    under the same name is a new Node object with a new uid, and so a new node here.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-kubernetes).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__kubernetes_node"
    ENTITY_NAME: ClassVar[str] = "Kubernetes Node"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "One Node object in a Kubernetes cluster, identified by the uid the cluster assigned it, with the "
        "versions its kubelet reports. The machine itself is the host it is backed by."
    )
    ENTITY_ICON: ClassVar[str] = "kubernetes-node"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "runtime"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("uid",)
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#1A3F8F", "border": "#0B1F4A", "label": "#FFFFFF"},
        }
    }

    # The machine behind the node outlives the Node object and may be described by other realms.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "computing_core__host"}], "edges": [{"type": "BACKED_BY_HOST__computing_core"}]},
    ]
    # Declared so the grid refuses any other inbound edge: a type that declares nothing is unconstrained.
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {
            "nodes": [{"type": "computing_core__kubernetes_cluster"}],
            "edges": [{"type": "REGISTERS_NODE__computing_core"}],
        },
        {
            "nodes": [{"type": "computing_core__kubernetes_pod"}],
            "edges": [{"type": "SCHEDULED_ON_NODE__computing_core"}],
        },
    ]

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "uid": {"type": "string", "minLength": 1},
        "name": {"type": "string"},
        "labels": LABELS_SCHEMA,
        "annotations": LABELS_SCHEMA,
        "kernel_version": {"type": ["string", "null"]},
        "kubernetes_version": {"type": ["string", "null"]},
        "kubelet_version": {"type": ["string", "null"]},
        "kube_proxy_version": {"type": ["string", "null"]},
        "container_runtime_version": {"type": ["string", "null"]},
        "architecture": {"type": ["string", "null"]},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "uid": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "labels": {"validation": "jsonschema", "schema": LABELS_SCHEMA},
        "annotations": {"validation": "jsonschema", "schema": LABELS_SCHEMA},
        "kernel_version": {"validation": "jsonschema", "schema": {"type": ["string", "null"]}},
        "kubernetes_version": {"validation": "jsonschema", "schema": {"type": ["string", "null"]}},
        "kubelet_version": {"validation": "jsonschema", "schema": {"type": ["string", "null"]}},
        "kube_proxy_version": {"validation": "jsonschema", "schema": {"type": ["string", "null"]}},
        "container_runtime_version": {"validation": "jsonschema", "schema": {"type": ["string", "null"]}},
        "architecture": {"validation": "jsonschema", "schema": {"type": ["string", "null"]}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["uid"]

    uid = models.CharField(
        max_length=64, blank=True, default="", help_text="metadata.uid as the cluster assigned it. Identity."
    )
    name = models.CharField(max_length=255, blank=True, default="", help_text="metadata.name; the node name.")
    labels = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text="metadata.labels as reported. Null = not observed; {} = the node has no labels.",
    )
    annotations = annotations_field("node")
    kernel_version = models.CharField(  # noqa: DJ001  (req-computing-core-kubernetes-9)
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="status.nodeInfo.kernelVersion. Null = not observed.",
    )
    kubernetes_version = models.CharField(  # noqa: DJ001  (req-computing-core-kubernetes-9)
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="the node's Kubernetes version as the source reports it. Null = not observed.",
    )
    kubelet_version = models.CharField(  # noqa: DJ001  (req-computing-core-kubernetes-9)
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="status.nodeInfo.kubeletVersion. Null = not observed.",
    )
    kube_proxy_version = models.CharField(  # noqa: DJ001  (req-computing-core-kubernetes-9)
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="status.nodeInfo.kubeProxyVersion. Null = not observed.",
    )
    container_runtime_version = models.CharField(  # noqa: DJ001  (req-computing-core-kubernetes-9)
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="status.nodeInfo.containerRuntimeVersion (containerd://1.7.2). Null = not observed.",
    )
    architecture = models.CharField(  # noqa: DJ001  (req-computing-core-kubernetes-9)
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text="status.nodeInfo.architecture (amd64, arm64). Null = not observed.",
    )

    class Meta(BaseModel.Meta):
        db_table = "computing_core__kubernetes_node"

    def validate(self) -> None:
        """No annotation key that carries a whole applied manifest is stored (req-computing-core-kubernetes-10)."""
        refuse_manifest_annotations(self.annotations)

    def get_name(self) -> str:
        return self.name or self.uid

    def __str__(self) -> str:
        return self.get_name()
