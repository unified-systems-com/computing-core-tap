"""Loopback Address — a loopback address on one host."""

import ipaddress
from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from tap_plugin.computing_core.addresses import LOOPBACK, host_scoped_kind

from tap_grid.models import BaseModel


class LoopbackAddress(BaseModel):
    """A loopback address (``127.0.0.0/8``, ``::1``) as one host has it.

    Every machine has its own ``127.0.0.1``, so a loopback address is not shareable the way an
    ``ip_address`` is, and ``ip_address`` refuses it (req-computing-core-ip-4). It lives here,
    keyed to its host the way ``os_user`` is: ``(host_realm, host_stable_id, address)``. The
    first two are the host's own natural key, carried as columns so the generated search can
    find the row (req-grid-entity-natural-key). ``127.0.0.1`` on two hosts is two nodes.

    The host draws ``DEFINES_LOOPBACK_ADDRESS`` to it, since its own network stack defines the
    address. It is a containment edge: the address exists only as part of the host and retires
    with it.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-loopback).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__loopback_address"
    ENTITY_NAME: ClassVar[str] = "Loopback Address"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A loopback address (127.0.0.0/8 or ::1) on one host. Every machine has its own, so it is "
        "keyed to its host and is not an ip_address: 127.0.0.1 on two hosts is two nodes."
    )
    ENTITY_ICON: ClassVar[str] = "loopback-address"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "network"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("host_realm", "host_stable_id", "address")
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "rectangle",
            "colors": {"fill": "#5A6E82", "border": "#2E3A46", "label": "#FFFFFF"},
        }
    }

    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "computing_core__host"}], "edges": [{"type": "DEFINES_LOOPBACK_ADDRESS__computing_core"}]},
    ]

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "host_realm": {"type": "string", "minLength": 1},
        "host_stable_id": {"type": "string", "minLength": 1},
        "address": {"type": "string"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "host_realm": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "host_stable_id": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "address": {"validation": "function"},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["host_realm", "host_stable_id", "address"]

    host_realm = models.CharField(max_length=64, blank=True, default="", help_text="The host's realm.")
    host_stable_id = models.CharField(max_length=255, blank=True, default="", help_text="The host's stable_id.")
    address = models.GenericIPAddressField(help_text="The loopback address: 127.0.0.0/8 or ::1.")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__loopback_address"

    def validate_address(self) -> None:
        """``address`` is a loopback address (req-computing-core-loopback-2)."""
        value = self.address
        if not isinstance(value, str):
            raise ValidationError({"address": ["address must be a string."]})
        try:
            kind = host_scoped_kind(value)
        except ValueError:
            raise ValidationError({"address": [f"{value!r} is not an IP address."]}) from None
        if kind != LOOPBACK:
            raise ValidationError(
                {"address": [f"{value} is not a loopback address (127.0.0.0/8 or ::1); a shareable address is an ip_address."]}
            )
        mapped = ipaddress.ip_address(value)
        if isinstance(mapped, ipaddress.IPv6Address) and mapped.ipv4_mapped is not None:
            # One address, one spelling: ::ffff:127.0.0.1 and 127.0.0.1 would be two keys for it.
            raise ValidationError({"address": [f"{value} is an IPv4-mapped address; write it as {mapped.ipv4_mapped}."]})

    def get_name(self) -> str:
        return self.address or ""

    def __str__(self) -> str:
        return self.get_name()
