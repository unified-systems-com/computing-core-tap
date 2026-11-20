"""Image Tag — a name in a registry that points at a container image."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel
from tap_plugin.computing_core.image_reference import canonical_repository


class ImageTag(BaseModel):
    """One tag in one repository of one registry: ``ghcr.io/org/app:1.2``.

    A container image is a ``host`` keyed by its digest (``req-computing-core-host``), and the
    digest is the image. A tag is a different thing: a name someone gave, in a registry, that
    points at an image and can be moved to another. One image has many tags, and one tag has
    pointed at many images over its life. So a tag is its own node, and the pointing is an edge.

    Identity is ``(registry, repository, tag)``. The registry and repository are stored in Docker's
    canonical form (:func:`~tap_plugin.computing_core.image_reference.canonical_repository`): ``nginx``
    with no registry is ``docker.io`` ``library/nginx``. So ECS's ``nginx:1.25`` and a scanner's
    ``docker.io/library/nginx:1.25`` are one tag (req-computing-core-image-tag-6). A writer sends the
    parts as written, with ``registry`` ``""`` when the reference named no host. The search and the
    save both apply the rule, so a short spelling finds the canonical row. The tag itself is kept as
    written. The key holds no digest: the tag is the same tag after it moves.

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
        # "" is a reference that named no registry: Docker Hub, filled in on save.
        "registry": {"type": "string", "maxLength": 255},
        "repository": {"type": "string", "minLength": 1, "maxLength": 255},
        "tag": {"type": "string", "minLength": 1, "maxLength": 128},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        name: {"validation": "jsonschema", "schema": schema}
        for name, schema in FIELD_CRUD_SCHEMA.items()
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["registry", "repository", "tag"]

    registry = models.CharField(max_length=255, help_text="The registry's host, and port where it has one, in canonical form (docker.io, ghcr.io, registry.example:5000). Docker Hub is docker.io however the writer spelled it.")
    repository = models.CharField(max_length=255, help_text="The repository path within the registry, in canonical form (org/app; library/nginx for Docker Hub's official nginx).")
    tag = models.CharField(max_length=128, help_text="The tag name, as written (1.2, latest). A tag is at most 128 characters by the OCI distribution specification.")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__image_tag"

    @classmethod
    def find_existing(cls, **properties: Any) -> BaseModel | None:
        """The generated search, over the canonical registry and repository (req-computing-core-image-tag-6).

        The rows hold the canonical form, so a writer's short spelling is made canonical before the
        search reads the columns. Otherwise ``("", "nginx", "1.25")`` would miss the row that
        ``("docker.io", "library/nginx", "1.25")`` wrote. Everything else is core's search, unchanged.
        """
        registry, repository = properties.get("registry"), properties.get("repository")
        if isinstance(registry, str) and isinstance(repository, str):
            properties["registry"], properties["repository"] = canonical_repository(registry, repository)
        return super().find_existing(**properties)

    def _canonicalise(self) -> bool:
        """Put the registry and repository in canonical form; True when that changed them.

        A part that is not a string is left alone, for validation to report.
        """
        if not (isinstance(self.registry, str) and isinstance(self.repository, str)):
            return False
        canonical = canonical_repository(self.registry, self.repository)
        if canonical == (self.registry, self.repository):
            return False
        self.registry, self.repository = canonical
        return True

    def full_validate(self) -> None:
        # The service layer validates (this, then Django's full_clean) before it saves, so the
        # canonical form is made here first: an empty registry is Docker Hub, not a blank field, and
        # the column limits are checked against what will be stored (req-computing-core-image-tag-6).
        self._canonicalise()
        super().full_validate()

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Store the canonical form, so every writer's spelling of one tag is one row
        # (req-computing-core-image-tag-6), on a save that skips validation too.
        if self._canonicalise():
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = list({*update_fields, "registry", "repository"})
        super().save(*args, **kwargs)

    def get_name(self) -> str:
        return f"{self.registry}/{self.repository}:{self.tag}" if self.registry and self.repository and self.tag else ""

    def __str__(self) -> str:
        return self.get_name()
