"""Port — a transport endpoint: a port number and transport family at one address on one network.

Identity is ``(network_name, address, transport, port_number)`` (req-computing-core-ports-5).
``network_name`` and ``address`` follow ``ip_address``: ``Internet`` for every public address,
the operator-declared network name for a private one. A shared port node holds identity only;
host-scoped addresses (loopback, link-local, wildcards) are not expected here (documented, not yet
enforced).
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class Port(BaseModel):
    """A transport endpoint, keyed by network, address, transport and port number."""

    ENTITY_TYPE: ClassVar[str] = "computing_core__port"
    ENTITY_NAME: ClassVar[str] = "Port"
    ENTITY_DESCRIPTION: ClassVar[str] = "A transport endpoint identified by port number and transport family."
    ENTITY_ICON: ClassVar[str] = "port"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "network"}
    # Identity (req-grid-entity-natural-key, req-computing-core-ports-5).
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("network_name", "address", "transport", "port_number")
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "rectangle",
            "colors": {"fill": "#8E7EB2", "border": "#5C4E82", "label": "#3E2A5F"},
            "label": {"valign": "center", "halign": "center", "position": "inside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string"},
        "network_name": {"type": "string", "minLength": 1},
        "address": {"type": "string"},
        # Part of the key, so required: a port whose number was not observed is not a port node
        # (req-computing-core-ports-2).
        "port_number": {"type": "integer"},
        "transport": {"type": "string"},
        "state": {"type": "string"},
    }

    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "network_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "address": {"validation": "jsonschema", "schema": {"type": "string"}},
        "port_number": {
            "validation": "jsonschema",
            "schema": {"type": "integer", "minimum": 0, "maximum": 65535},
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
    CREATE_REQUIRED: ClassVar[list[str]] = ["network_name", "address", "transport", "port_number"]

    name = models.CharField(max_length=255, blank=True, default="")
    # The address space and address this port is on; see ip_address.
    network_name = models.CharField(max_length=255)
    address = models.GenericIPAddressField()
    port_number = models.PositiveIntegerField(db_index=True)
    transport = models.CharField(max_length=8, default="tcp")
    state = models.CharField(max_length=32, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__port"

    def get_name(self) -> str:
        if self.name:
            return self.name
        host = f"[{self.address}]" if ":" in str(self.address) else self.address
        return f"{host}:{self.port_number}/{self.transport}"

    def __str__(self) -> str:
        return self.get_name()
