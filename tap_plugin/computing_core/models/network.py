"""Network — a named address space: the value of the ``tap.computing.network_name`` dimension."""

import ipaddress
from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models

from tap_grid.event_time import NO_EVENT_TIME
from tap_grid.models import BaseModel


def normalise_ranges(ranges: list[str]) -> list[str]:
    """Canonical text for each range, duplicates dropped, IPv4 before IPv6, then by address.

    Raises ValueError for a value that is not a CIDR range, or one with host bits set
    (``10.0.0.1/8`` could mean an address or a range, so it is refused rather than guessed).
    """
    networks = {ipaddress.ip_network(r, strict=True) for r in ranges}
    return [str(n) for n in sorted(networks, key=lambda n: (n.version, n.network_address, n.prefixlen))]


class Network(BaseModel):
    """One address space in which an address names one machine: a VPC, a corporate network, the Internet.

    ``name`` is the value an address-bearing node carries in the ``tap.computing.network_name``
    dimension, so ``10.0.0.5`` in one network and ``10.0.0.5`` in another are two nodes. It is
    the network's identity and is fixed once written: renaming a network would silently move
    every address keyed to it, so a new name is a new network.

    ``ranges`` lists the CIDR ranges the network holds, IPv4 and IPv6, stored in canonical text
    and sorted. A network can hold many ranges, and a range can belong to a network that spans
    several VPCs. Null means the ranges were not stated; the Internet network states none.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-network).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__network"
    ENTITY_NAME: ClassVar[str] = "Network"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A named address space in which an address names one machine: a VPC, a corporate network, "
        "the Internet. Its name is the value of the tap.computing.network_name dimension and is fixed "
        "once written. Holds the CIDR ranges it covers."
    )
    ENTITY_ICON: ClassVar[str] = "network"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "network"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("name",)
    # No event time: a named network and its ranges carry no time field.
    EVENT_TIME: ClassVar[Any] = NO_EVENT_TIME
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#3E5A78", "border": "#1F2E3D", "label": "#FFFFFF"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string", "minLength": 1, "maxLength": 255},
        "description": {"type": "string"},
        "ranges": {"type": ["array", "null"], "items": {"type": "string"}},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "function"},
        "description": {"validation": "jsonschema", "schema": {"type": "string"}},
        "ranges": {"validation": "function"},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["name"]

    name = models.CharField(
        max_length=255,
        help_text="The network's name: the value of tap.computing.network_name. Identity; fixed once written.",
    )
    description = models.TextField(blank=True, default="", help_text="What this network is, for a human reader.")
    ranges = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text="CIDR ranges the network holds, IPv4 and IPv6, in canonical text, sorted. Null = not stated.",
    )

    class Meta(BaseModel.Meta):
        db_table = "computing_core__network"

    def validate_name(self) -> None:
        """``name`` is non-blank and does not change once the network exists (req-computing-core-network-3)."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError({"name": ["name is required."]})
        if len(self.name) > 255:
            raise ValidationError({"name": ["name is at most 255 characters."]})
        if self.pk is None:
            return
        stored = type(self).objects.filter(pk=self.pk).values_list("name", flat=True).first()
        if stored is not None and stored != self.name:
            raise ValidationError(
                {
                    "name": [
                        f"a network's name is fixed once written ({stored!r}); every address in it is "
                        "keyed by that name. Create a new network for the new name."
                    ]
                }
            )

    def validate_ranges(self) -> None:
        """``ranges`` is null or a list of CIDR ranges with no host bits set (req-computing-core-network-2)."""
        if self.ranges is None:
            return
        if not isinstance(self.ranges, list) or not all(isinstance(r, str) for r in self.ranges):
            raise ValidationError({"ranges": ["ranges must be a list of CIDR strings."]})
        bad = []
        for value in self.ranges:
            try:
                ipaddress.ip_network(value, strict=True)
            except ValueError:
                bad.append(value)
        if bad:
            raise ValidationError(
                {"ranges": [f"not a CIDR range, or host bits are set: {', '.join(repr(b) for b in bad)}."]}
            )

    def prepare_for_write(self) -> None:
        """Store each range in one canonical form, so two observers' spellings of a range agree.

        Core calls this before it validates and before it compares a write with the stored row,
        so a re-observation spelled ``2001:DB8::/32`` is compared as ``2001:db8::/32`` and changes
        nothing (computing-core#93). It is idempotent: canonical ranges come back unchanged. A list
        that is not all strings, or holds a value that is not a range, is left as written for
        :meth:`validate_ranges` to refuse; ``ipaddress`` would otherwise turn ``10`` into a range.
        """
        super().prepare_for_write()
        if isinstance(self.ranges, list) and all(isinstance(r, str) for r in self.ranges):
            try:
                self.ranges = normalise_ranges(self.ranges)
            except ValueError:
                pass  # validate_ranges() reports it

    def get_name(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.get_name()
