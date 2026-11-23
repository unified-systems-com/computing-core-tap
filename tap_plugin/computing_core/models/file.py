"""File — a filesystem object tracked as a durable artifact."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.event_time import NO_EVENT_TIME
from tap_grid.models import BaseModel


class File(BaseModel):
    """A filesystem object tracked as a durable artifact when meaningful."""

    ENTITY_TYPE: ClassVar[str] = "computing_core__file"
    ENTITY_NAME: ClassVar[str] = "File"
    ENTITY_DESCRIPTION: ClassVar[str] = "A filesystem object tracked as a durable artifact."
    ENTITY_ICON: ClassVar[str] = "file"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "storage"}
    # No event time: the model holds no file timestamp (mtime, ctime).
    EVENT_TIME: ClassVar[Any] = NO_EVENT_TIME
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "rectangle",
            "colors": {"fill": "#B2A05E", "border": "#837228", "label": "#FFFFFF"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string"},
        "file_path": {"type": "string"},
        "file_type": {"type": "string"},
        "version": {"type": "string"},
    }

    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "file_path": {"validation": "jsonschema", "schema": {"type": "string"}},
        "file_type": {"validation": "jsonschema", "schema": {"type": "string"}},
        "version": {"validation": "jsonschema", "schema": {"type": "string"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["file_path"]

    name = models.CharField(max_length=255, blank=True, default="")
    file_path = models.CharField(max_length=1024, blank=True, default="", db_index=True)
    file_type = models.CharField(max_length=64, blank=True, default="")
    version = models.CharField(max_length=64, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__file"

    def get_name(self) -> str:
        return self.name or self.file_path

    def __str__(self) -> str:
        return self.get_name()
