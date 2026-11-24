"""Port — a transport endpoint identified by port number and transport family."""

from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from tap_plugin.computing_core.addresses import host_scoped_kind

from tap_plugin.computing_core.key_dimensions import NETWORK_NAME_ENTRY
from tap_plugin.computing_core.models.ip_address import REFUSED_KINDS

from tap_grid.event_time import NO_EVENT_TIME
from tap_grid.models import BaseModel


class Port(BaseModel):
    """A transport endpoint: a port number and transport at one address on one network.

    Identity is ``(tap.computing.network_name, address, transport, port_number)``
    (req-computing-core-ports-5). The network is stamped on the envelope, as for ``ip_address``.
    ``state`` stays outside the key.
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__port"
    ENTITY_NAME: ClassVar[str] = "Port"
    ENTITY_DESCRIPTION: ClassVar[str] = "A transport endpoint identified by port number and transport family."
    ENTITY_ICON: ClassVar[str] = "port"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "network"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = (NETWORK_NAME_ENTRY, "address", "transport", "port_number")
    # No event time: a port carries no time field.
    EVENT_TIME: ClassVar[Any] = NO_EVENT_TIME
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "rectangle",
            "colors": {"fill": "#8E7EB2", "border": "#5C4E82", "label": "#3E2A5F"},
            "label": {"valign": "center", "halign": "center", "position": "inside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string"},
        "address": {"type": "string", "minLength": 1},
        "port_number": {
            "type": ["integer", "null"],
            # Declared absence semantics (tap_grid req-grid-node-observation-6). An integer
            # field, so two-state (null | value): null = port number unobserved. The ephemeral
            # client-port signal ("number unknown but known to be ephemeral") is a separate
            # observation, deferred to a future is_ephemeral/role field — NOT a meaning of null
            # and NOT a sentinel (no -1). not_applicable stays unpermitted: null already covers
            # the absence, so N/A adds no useful flavor. See req-computing-core-ports-2.
            "x-tap-absence": {
                "null_default": "unobserved",
                "empty_is_meaningful": False,
                "convention": "req-computing-core-ports-2",
                "description": "Null = port number unobserved (not captured by the observing source).",
                "not_applicable": {"permitted": False},
            },
        },
        "transport": {"type": "string"},
        "state": {"type": "string"},
    }

    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "address": {"validation": "function"},
        "port_number": {
            "validation": "jsonschema",
            "schema": {"type": ["integer", "null"], "minimum": 0, "maximum": 65535},
        },
        "transport": {
            "validation": "jsonschema",
            "schema": {"type": "string", "enum": ["tcp", "udp", "sctp"]},
        },
        "state": {
            "validation": "jsonschema",
            "schema": {"type": "string", "enum": ["listening", "bound", "connected", "closed", ""]},
        },
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["address", "transport", "port_number"]

    name = models.CharField(max_length=255, blank=True, default="")
    address = models.GenericIPAddressField(help_text="The address the port is on, within its network.")
    port_number = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    transport = models.CharField(max_length=8, default="tcp")
    state = models.CharField(max_length=32, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__port"

    def validate_address(self) -> None:
        """``address`` is shareable, as on ``ip_address`` (req-computing-core-ports-5, -ip-4): a loopback,
        wildcard or link-local address names a different endpoint on every machine, so a shared port
        node keyed on one would join unrelated hosts."""
        value = self.address
        if not isinstance(value, str) or not value:
            raise ValidationError({"address": ["address is required and must be a string."]})
        try:
            kind = host_scoped_kind(value)
        except ValueError:
            raise ValidationError({"address": [f"{value!r} is not an IP address."]}) from None
        if kind is not None:
            raise ValidationError({"address": [f"{value} {REFUSED_KINDS[kind]}"]})

    def validate(self) -> None:
        """``port_number`` is part of the key, so a port is written only once its number is observed
        (req-computing-core-ports-5). Null still means unobserved (ports-2), but a key with a hole would
        mint a new node on every run instead of finding the last one."""
        if self.port_number is None:
            raise ValidationError({"port_number": ["port_number is part of the port's key and must be observed."]})

    def get_name(self) -> str:
        if self.name:
            return self.name
        num = self.port_number if self.port_number is not None else "*"
        return f":{num}/{self.transport}"

    def __str__(self) -> str:
        return self.get_name()
