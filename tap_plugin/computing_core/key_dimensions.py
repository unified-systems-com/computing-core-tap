"""The identity-bearing dimensions computing_core's natural keys name (form 3, unified-systems-com/tap#1355).

A key entry that names a dimension (``tap_grid.natural_key.dimension_entry``) is read from the
writer's envelope dimensions, never from the payload, and is fixed on the row once written. Each
dimension here is declared in ``grift/dimension.grift.json`` with ``usable_in_keys: true``; core
refuses a key that names one without it (``req-grid-dimension-knobs-3``).

Before form 3, plain string columns stood in for these dimensions: a second vocabulary that was
declared nowhere. This module derives no ids; it only names the dimensions.

Spec: specs/spec-computing-core-v0.md (req-computing-core-dimensions, req-computing-core-host).
"""

from typing import Final

from tap_grid.natural_key import dimension_entry

#: Whose numbering a host's ``stable_id`` comes from (req-computing-core-host).
HOST_TYPE: Final[str] = "tap.computing.host_type"
#: Whose numbering a cluster's ``stable_id`` comes from (req-computing-core-kubernetes).
KUBERNETES_CLUSTER_TYPE: Final[str] = "tap.computing.kubernetes_cluster_type"
#: The host a host-scoped thing belongs to, valued by the host's spine natural key (req-computing-core-dimensions-6).
HOST: Final[str] = "tap.computing.host"
#: The address space an address belongs to (req-computing-core-dimensions).
NETWORK_NAME: Final[str] = "tap.computing.network_name"

HOST_TYPE_ENTRY: Final[str] = dimension_entry(HOST_TYPE)
KUBERNETES_CLUSTER_TYPE_ENTRY: Final[str] = dimension_entry(KUBERNETES_CLUSTER_TYPE)
HOST_ENTRY: Final[str] = dimension_entry(HOST)
NETWORK_NAME_ENTRY: Final[str] = dimension_entry(NETWORK_NAME)

#: The host types in use, and the bounded value list of ``tap.computing.host_type``. Adding one is a
#: change to the seed and to the spec's "Host types in use" table, in the change that first uses it.
HOST_TYPES: Final[tuple[str, ...]] = (
    "aws-ec2",
    "github-runner",
    "machine-id",
    "assert",
    "oci-digest",
    "kubernetes-node-uid",
)
#: The cluster types in use, and the bounded value list of ``tap.computing.kubernetes_cluster_type``.
KUBERNETES_CLUSTER_TYPES: Final[tuple[str, ...]] = ("kube-system-uid", "assert", "anchore-inventory")
