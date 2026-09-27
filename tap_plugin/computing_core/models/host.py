"""Host — an environment that runs an operating system and executes programs."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel

#: OCSF's device ``type_id`` captions that name a machine an operating system runs on (OCSF 1.6.0,
#: ``objects/endpoint.json``), lower-cased, plus ``container``, which OCSF models as a separate object.
#: Blank means nobody has said; ``unknown`` means a source was asked and could not say (OCSF 0).
FORM_FACTORS: tuple[str, ...] = (
    "",
    "desktop",
    "laptop",
    "tablet",
    "mobile",
    "server",
    "virtual",
    "container",
    "iot",
    "unknown",
)
OWNERSHIPS: tuple[str, ...] = ("", "corporate", "personal")


class Host(BaseModel):
    """An OS-bearing environment: an end-user device, a server, a virtual machine, a container or a runner.

    The neutral machine that an identity acts from and a job runs on. Vendor device records (an
    Okta device, a Duo endpoint, a Teleport trusted device) are separate nodes that point here with
    ``REPRESENTS_HOST__computing_core``; the person the machine is issued to is reached with
    ``ASSIGNED_TO_HUMAN__computing_core``. Physical versus virtual is the ``form_factor`` value, not a
    separate type, because a collector often cannot tell which (req-computing-core-host).

    Spec: specs/spec-computing-core-v0.md (req-computing-core-host).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__host"
    ENTITY_NAME: ClassVar[str] = "Host"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "An environment that runs an operating system and executes programs: a laptop, a phone, a server, "
        "a virtual machine, a container or a CI runner."
    )
    ENTITY_ICON: ClassVar[str] = "host"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "host"}
    # The asset tag is assigned, so every form factor has one, and it survives a rename, an OS
    # reinstall and a disk swap. A hardware serial is not used: a container has none, a VM's is
    # blank or cloned, and it is unique only per manufacturer (req-computing-core-host-2).
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("asset_tag",)
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#3B6E5A", "border": "#1F3D31", "label": "#FFFFFF"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "asset_tag": {"type": "string", "minLength": 1},
        "name": {"type": "string"},
        "form_factor": {"type": "string", "enum": list(FORM_FACTORS)},
        "os": {"type": "string"},
        "managed": {"type": ["boolean", "null"]},
        "ownership": {"type": "string", "enum": list(OWNERSHIPS)},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "asset_tag": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "form_factor": {"validation": "jsonschema", "schema": {"type": "string", "enum": list(FORM_FACTORS)}},
        "os": {"validation": "jsonschema", "schema": {"type": "string"}},
        "managed": {"validation": "jsonschema", "schema": {"type": ["boolean", "null"]}},
        "ownership": {"validation": "jsonschema", "schema": {"type": "string", "enum": list(OWNERSHIPS)}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["asset_tag"]

    #: The operator's stable identifier for this machine: an inventory asset tag for a device, or the
    #: assigning system's stable name for a runner or container. Identity; never a display name.
    asset_tag = models.CharField(max_length=255, blank=True, default="", db_index=True)
    #: Display name (a hostname, a runner name). Not identity: it changes on rename.
    name = models.CharField(max_length=255, blank=True, default="")
    #: One of FORM_FACTORS. Blank is not observed; ``unknown`` is observed and unclassifiable.
    form_factor = models.CharField(max_length=32, blank=True, default="")
    #: The operating system as reported (``macOS 15.6``, ``linux``). Free text until an
    #: ``operating_system`` node exists.
    os = models.CharField(max_length=255, blank=True, default="")
    #: Enrolled in device management (MDM). Null means not observed; false means observed unenrolled.
    managed = models.BooleanField(null=True, blank=True)
    #: ``corporate`` or ``personal`` (bring-your-own). Blank means not observed.
    ownership = models.CharField(max_length=16, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "computing_core__host"

    def get_name(self) -> str:
        return self.name or self.asset_tag or ""

    def __str__(self) -> str:
        return self.get_name()
