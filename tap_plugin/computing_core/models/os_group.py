"""OS Group — a group in one host's own account database."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class OsGroup(BaseModel):
    """A group that lives on one host: an ``/etc/group`` entry, a Windows local group.

    Membership is ``<os_user> MEMBER_OF_GROUP <os_group>``. Group membership is how a host grants
    most of what an account can do (``wheel``, ``sudo``, ``docker``, ``Administrators``), so an
    access review reads it from here.

    Identity is ``(host_realm, host_stable_id, local_id)``, chosen as for ``os_user``:

    - **Windows:** the group SID, so a renamed group stays one node. A builtin group's
      well-known SID (``S-1-5-32-544`` for Administrators) is the same on every machine, which
      is one reason the host is part of the key.
    - **POSIX:** the group name, so **renaming a POSIX group (``groupmod -n``) produces a new
      node**. The old node retires once its host's collector no longer observes it, and its
      membership edges stay with it. The gid is not used as the key: two group names may share
      a gid, which would merge them into one node and fail the batch that observes both, and a
      freed gid is re-issued to the next group created.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-os-accounts).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__os_group"
    ENTITY_NAME: ClassVar[str] = "OS Group"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A group defined in one host's own account database: a Linux /etc/group entry or a "
        "Windows local group. Its members are OS users on the same host. Keyed to its host by "
        "local_id. On Windows that is the SID, so a renamed group stays the same node. On POSIX "
        "it is the group name, so a renamed group becomes a new node and the old one retires. "
        "The gid is not the key: two names can share a gid and freed gids are re-issued."
    )
    ENTITY_ICON: ClassVar[str] = "os-group"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "identity"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("host_realm", "host_stable_id", "local_id")
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#B26B8E", "border": "#5C2B45", "label": "#FFFFFF"},
        }
    }

    # Endpoint rules for this plugin's own edges; a foreign edge type whose own endpoint list is
    # open or names this type is still admitted by the grid's permission union.
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "computing_core__host"}], "edges": [{"type": "DEFINES_OS_GROUP__computing_core"}]},
        {"nodes": [{"type": "computing_core__os_user"}], "edges": [{"type": "MEMBER_OF_GROUP__computing_core"}]},
    ]

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "host_realm": {"type": "string", "minLength": 1},
        "host_stable_id": {"type": "string", "minLength": 1},
        "local_id": {"type": "string", "minLength": 1},
        "name": {"type": "string"},
        "gid": {"type": ["integer", "null"], "minimum": 0},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "host_realm": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "host_stable_id": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "local_id": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "gid": {"validation": "jsonschema", "schema": {"type": ["integer", "null"], "minimum": 0}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["host_realm", "host_stable_id", "local_id"]

    host_realm = models.CharField(max_length=64, blank=True, default="", help_text="The defining host's realm.")
    host_stable_id = models.CharField(
        max_length=255, blank=True, default="", help_text="The defining host's stable_id."
    )
    local_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The SID on Windows; the group name on POSIX. Identity within the host.",
    )
    name = models.CharField(max_length=255, blank=True, default="", help_text="The group name as reported.")
    gid = models.PositiveIntegerField(
        null=True, blank=True, default=None, help_text="POSIX numeric group id. Null on Windows or when not observed."
    )

    class Meta(BaseModel.Meta):
        db_table = "computing_core__os_group"

    def get_name(self) -> str:
        return self.name or self.local_id

    def __str__(self) -> str:
        return self.get_name()
