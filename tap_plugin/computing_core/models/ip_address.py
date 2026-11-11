"""IP Address — a generic IPv4 or IPv6 address, found by the network it is reachable on and the address.

Identity is ``(network_name, address)`` (req-computing-core-ip-4). ``network_name`` names the
address space: ``Internet`` for every public address, and for a private address the network name
the operator declares in each collector's config, so one VPC routed from corp is one network in
every source. ``address`` is a ``GenericIPAddressField``, which canonicalizes on clean, so two
spellings of one IPv6 address are one node.

Host-scoped addresses (loopback, link-local, the wildcards 0.0.0.0 and ::) are not expected here:
a ``127.0.0.1`` is a different thing on every host, and a source that sees one records it against
that host. That expectation is documented, not yet enforced (req-computing-core-ip-5).
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class IpAddress(BaseModel):
    """A generic IPv4 or IPv6 address, keyed by the network it is on and the address."""

    ENTITY_TYPE: ClassVar[str] = "computing_core__ip_address"
    ENTITY_NAME: ClassVar[str] = "IP Address"
    ENTITY_DESCRIPTION: ClassVar[str] = "A generic IPv4 or IPv6 address."
    ENTITY_ICON: ClassVar[str] = "ip-address"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "network"}
    # Identity (req-grid-entity-natural-key, req-computing-core-ip-4): the network the address is
    # reachable on, then the address. `Internet` for every public address.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("network_name", "address")
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "rectangle",
            "colors": {"fill": "#7A9EC2", "border": "#4A6E92", "label": "#FFFFFF"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string"},
        "network_name": {"type": "string", "minLength": 1},
        "address": {"type": "string"},
        "version": {"type": "integer"},
    }

    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "network_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "address": {"validation": "jsonschema", "schema": {"type": "string"}},
        "version": {"validation": "jsonschema", "schema": {"type": "integer", "enum": [4, 6]}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["network_name", "address"]

    name = models.CharField(max_length=255, blank=True, default="")
    # The address space: `Internet` for a public address, else the operator-declared network name.
    network_name = models.CharField(max_length=255)
    address = models.GenericIPAddressField(db_index=True)
    version = models.PositiveSmallIntegerField(default=4)

    class Meta(BaseModel.Meta):
        db_table = "computing_core__ip_address"

    def get_name(self) -> str:
        return self.name or self.address

    def __str__(self) -> str:
        return self.get_name()
