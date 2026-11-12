"""IP Address — a generic IPv4 or IPv6 address."""

from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from tap_plugin.computing_core.addresses import LINK_LOCAL, LOOPBACK, WILDCARD, host_scoped_kind

from tap_grid.models import BaseModel

#: Why each host- or link-scoped kind is refused here, and where it belongs (req-computing-core-ip-4).
REFUSED_KINDS: dict[str, str] = {
    LOOPBACK: (
        "is a loopback address: every machine has its own, so a shared ip_address node would join "
        "unrelated hosts. Record it as computing_core__loopback_address, keyed to its host."
    ),
    WILDCARD: (
        "is a wildcard address: it means every address on a host, not one address. Record the "
        "listener on its host instead."
    ),
    LINK_LOCAL: (
        "is a link-local address: it is valid only on one network segment and is reused on every "
        "segment, so a shared ip_address node would join unrelated machines."
    ),
}


class IpAddress(BaseModel):
    """A generic IPv4 or IPv6 address, shareable across observers.

    Loopback, wildcard and link-local addresses are refused (req-computing-core-ip-4): their
    meaning depends on the machine or link they are seen from. Loopback belongs on
    ``loopback_address``.
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__ip_address"
    ENTITY_NAME: ClassVar[str] = "IP Address"
    ENTITY_DESCRIPTION: ClassVar[str] = "A generic IPv4 or IPv6 address."
    ENTITY_ICON: ClassVar[str] = "ip-address"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "network"}
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "rectangle",
            "colors": {"fill": "#7A9EC2", "border": "#4A6E92", "label": "#FFFFFF"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string"},
        "address": {"type": "string"},
        "version": {"type": "integer"},
    }

    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "address": {"validation": "function"},
        "version": {"validation": "jsonschema", "schema": {"type": "integer", "enum": [4, 6]}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["address"]

    name = models.CharField(max_length=255, blank=True, default="")
    address = models.GenericIPAddressField(db_index=True)
    version = models.PositiveSmallIntegerField(default=4)

    class Meta(BaseModel.Meta):
        db_table = "computing_core__ip_address"

    def validate_address(self) -> None:
        """``address`` is an IP address that one observer can share with another."""
        value = self.address
        if not isinstance(value, str):
            raise ValidationError({"address": ["address must be a string."]})
        try:
            kind = host_scoped_kind(value)
        except ValueError:
            raise ValidationError({"address": [f"{value!r} is not an IP address."]}) from None
        if kind is not None:
            raise ValidationError({"address": [f"{value} {REFUSED_KINDS[kind]}"]})

    def get_name(self) -> str:
        return self.name or self.address

    def __str__(self) -> str:
        return self.get_name()
