"""Image Tag — a name in a registry that points at a container image."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class ImageTag(BaseModel):
    """One tag in one repository of one registry: ``ghcr.io/org/app:1.2``.

    A container image is a ``host`` keyed by its digest (``req-computing-core-host``), and the
    digest is the image. A tag is a different thing: a name someone gave, in a registry, that
    points at an image and can be moved to another. One image has many tags, and one tag has
    pointed at many images over its life. So a tag is its own node, and the pointing is an edge.

    Identity is ``(registry, repository, tag)``, each as the registry spells it. The key holds no
    digest: the tag is the same tag after it moves.

    ``TAGS_IMAGE`` says an observer saw this tag on that image. It does not say the tag points
    there now: a tag that has moved keeps the edge to each image it was seen on, and the edge's
    ``detected_at`` is when the observer says it saw it. Which image a tag names today is the
    registry's to answer.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-image-tag).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__image_tag"
    ENTITY_NAME: ClassVar[str] = "Image Tag"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A tag in a container registry: a registry, a repository and a tag name, which together are a "
        "name that points at an image and can be moved. The image itself is the host keyed by its digest."
    )
    ENTITY_ICON: ClassVar[str] = "image-tag"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "runtime"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("registry", "repository", "tag")
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#4A6F8A", "border": "#22394A", "label": "#FFFFFF"},
        }
    }

    # A tag points at images; the image is a reference, never contained: it outlives every name it has had.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "computing_core__host"}], "edges": [{"type": "TAGS_IMAGE__computing_core"}]},
    ]

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "registry": {"type": "string", "minLength": 1, "maxLength": 255},
        "repository": {"type": "string", "minLength": 1, "maxLength": 255},
        "tag": {"type": "string", "minLength": 1, "maxLength": 128},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        name: {"validation": "jsonschema", "schema": schema}
        for name, schema in FIELD_CRUD_SCHEMA.items()
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["registry", "repository", "tag"]

    registry = models.CharField(max_length=255, help_text="The registry's host, and port where it has one, as written in the reference (ghcr.io, registry.example:5000).")
    repository = models.CharField(max_length=255, help_text="The repository path within the registry, as written (org/app).")
    tag = models.CharField(max_length=128, help_text="The tag name, as written (1.2, latest). A tag is at most 128 characters by the OCI distribution specification.")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__image_tag"

    def get_name(self) -> str:
        return f"{self.registry}/{self.repository}:{self.tag}" if self.registry and self.repository and self.tag else ""

    def __str__(self) -> str:
        return self.get_name()
