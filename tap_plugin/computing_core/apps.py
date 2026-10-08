"""TAP Computing Core plugin AppConfig."""

from tap_plugins.base import TapPluginConfig

#: Slug -> why it was removed. Recorded with core's retired-type registry in ready(), so a seed
#: from an older plugin pin that still carries one of these nodes is stripped at the seeding
#: boundary with this reason instead of failing the boot (tap_grid/grift/retired.py).
RETIRED_ENTITY_TYPES: dict[str, str] = {
    "computing_core__user": (
        "removed 2026-10-08 (computing-core#27): a person is identity_core__human, "
        "and an account on a host is computing_core__os_user; re-publish the bundle with the "
        "node as identity_core__human (or os_user, if it was an account) and drop the user node"
    ),
}


class ComputingCoreConfig(TapPluginConfig):
    def ready(self) -> None:
        super().ready()
        from tap_grid.registry import retire_entity_type

        for slug, reason in RETIRED_ENTITY_TYPES.items():
            retire_entity_type(slug, reason)
