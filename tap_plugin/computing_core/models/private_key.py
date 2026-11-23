"""Private Key — a private cryptographic key."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.event_time import NO_EVENT_TIME
from tap_grid.models import BaseModel


class PrivateKey(BaseModel):
    """A private cryptographic key represented as a data blob."""

    ENTITY_TYPE: ClassVar[str] = "computing_core__private_key"
    ENTITY_NAME: ClassVar[str] = "Private Key"
    ENTITY_DESCRIPTION: ClassVar[str] = "A private cryptographic key."
    ENTITY_ICON: ClassVar[str] = "private-key"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "storage"}
    # No event time: the model holds no generation or validity time.
    EVENT_TIME: ClassVar[Any] = NO_EVENT_TIME
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "rectangle",
            "colors": {"fill": "#8E5E5E", "border": "#5C2B2B", "label": "#FFFFFF"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string"},
        "algorithm": {"type": "string"},
        "key_size": {"type": ["integer", "null"]},
        "fingerprint": {"type": "string"},
    }

    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "algorithm": {"validation": "jsonschema", "schema": {"type": "string"}},
        "key_size": {"validation": "jsonschema", "schema": {"type": ["integer", "null"]}},
        "fingerprint": {"validation": "jsonschema", "schema": {"type": "string"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = []

    name = models.CharField(max_length=255, blank=True, default="")
    algorithm = models.CharField(max_length=32, blank=True, default="")
    key_size = models.PositiveIntegerField(blank=True, null=True)
    fingerprint = models.CharField(max_length=255, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__private_key"

    def get_name(self) -> str:
        return self.name or self.fingerprint or "private key"

    def __str__(self) -> str:
        return self.get_name()
