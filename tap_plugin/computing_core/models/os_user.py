"""OS User — an account in one host's own account database."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class OsUser(BaseModel):
    """An account that lives on one host: a ``/etc/passwd`` entry, a Windows local SAM account.

    Not a person. A person is ``identity_core__human``; this account points at one with
    ``HELD_BY_HUMAN__identity_core`` when someone who knows asserts it, exactly as an Okta or
    GitLab account does. A directory account (Active Directory, LDAP) that a host merely
    resolves is not an ``os_user``: it is defined by the directory, not by the host.

    Identity is ``(host_realm, host_stable_id, local_id)``. The first two are the host's own
    natural key, carried as columns so the generated search can find the row
    (req-grid-entity-natural-key). ``local_id`` is the identifier the host's account database
    itself uses to tell accounts apart and does not re-issue:

    - **Windows:** the account SID (``S-1-5-21-…-1001``). A rename keeps the SID, so renaming
      ``Administrator`` (a common hardening step) stays one node with a history of names.
    - **POSIX:** the login name, so **renaming a POSIX account (``usermod -l``) produces a new
      node**. The old node retires once its host's collector no longer observes it; its history
      and edges stay with it and do not carry over. The uid is not used as the key for two
      reasons. POSIX allows two names to share one uid (``root`` and ``toor``), so a uid key
      would merge two accounts into one node and fail any batch that observes both. And a freed uid is re-issued to the next
      account created, so a uid key would hand a deleted account's history and edges to a
      stranger. The account database behaves the same way: every file that names the old login
      (sudoers, ``authorized_keys`` paths) stops matching.

    On POSIX ``local_id`` and ``name`` hold the same string. They are two facts that coincide
    there: ``local_id`` is identity, ``name`` is the reported display name, and on Windows they
    differ.

    Spec: specs/spec-computing-core-v0.md (req-computing-core-os-accounts).
    """

    ENTITY_TYPE: ClassVar[str] = "computing_core__os_user"
    ENTITY_NAME: ClassVar[str] = "OS User"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "An account defined in one host's own account database: a Linux /etc/passwd entry or a "
        "Windows local account. Not a person; it points at one with HELD_BY_HUMAN. Keyed to its "
        "host by local_id. On Windows that is the SID, so a renamed account stays the same node. "
        "On POSIX it is the login name, so a renamed account becomes a new node and the old one "
        "retires. The uid is not the key: two names can share a uid (root/toor) and freed uids "
        "are re-issued."
    )
    ENTITY_ICON: ClassVar[str] = "os-user"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"tap.computing": "identity"}
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("host_realm", "host_stable_id", "local_id")
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "ellipse",
            "colors": {"fill": "#B26B8E", "border": "#5C2B45", "label": "#FFFFFF"},
        }
    }

    # Endpoint rules for this plugin's own edges (the grid's permission union still admits a
    # foreign edge type whose own endpoint list is open or names this type, such as
    # HELD_BY_HUMAN__identity_core, whose source side is open).
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "computing_core__os_group"}], "edges": [{"type": "MEMBER_OF_GROUP__computing_core"}]},
    ]
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "computing_core__host"}], "edges": [{"type": "DEFINES_OS_USER__computing_core"}]},
    ]

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "host_realm": {"type": "string", "minLength": 1},
        "host_stable_id": {"type": "string", "minLength": 1},
        "local_id": {"type": "string", "minLength": 1},
        "name": {"type": "string"},
        "uid": {"type": ["integer", "null"], "minimum": 0},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "host_realm": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "host_stable_id": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "local_id": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "uid": {"validation": "jsonschema", "schema": {"type": ["integer", "null"], "minimum": 0}},
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
        help_text="The SID on Windows; the login name on POSIX. Identity within the host.",
    )
    name = models.CharField(max_length=255, blank=True, default="", help_text="The account name as reported.")
    uid = models.PositiveIntegerField(
        null=True, blank=True, default=None, help_text="POSIX numeric user id. Null on Windows or when not observed."
    )

    class Meta(BaseModel.Meta):
        db_table = "computing_core__os_user"

    def get_name(self) -> str:
        return self.name or self.local_id

    def __str__(self) -> str:
        return self.get_name()
