"""Delete edges of the two web-document edge types retired on 2026-10-02 (computing-core#25).

`FETCHES_DOCUMENT` (any fetcher -> web_document) and `HOSTS_DOCUMENT` (web_host -> web_document)
are removed rather than renamed. An HTTP interaction will be modelled as a verb node (get, put,
patch, ...) with its own edges from the originator and to the destination, not as one edge
between them; HOSTS_DOCUMENT goes with it (George's ruling, highbar Q133). computing_core emits
neither itself, but samsite seeds HOSTS_DOCUMENT and its compliance collector emits
FETCHES_DOCUMENT, so a grid upgraded in place still carries rows of both. With the definitions
gone they would linger as undefined types nothing reads; this removes them with their spine
rows. Nodes are untouched: the `web_host` and `web_document` nodes stay.

Same shape as 0003_retire_renamed_edge_types. Direct ORM access is the sanctioned path in
migrations.
"""

from typing import Any

from django.db import migrations

_RETIRED_EDGE_TYPES = (
    "FETCHES_DOCUMENT__computing_core",
    "HOSTS_DOCUMENT__computing_core",
)


def delete_retired_edges(apps: Any, schema_editor: Any) -> None:
    Edge = apps.get_model("tap_grid", "Edge")
    Entity = apps.get_model("tap_grid", "Entity")
    edges = Edge.objects.filter(edge_type__in=_RETIRED_EDGE_TYPES)
    entity_ids = list(edges.values_list("entity_id", flat=True))
    edges.delete()
    Entity.objects.filter(pk__in=entity_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("computing_core", "0004_drop_unused_configuration"),
        ("tap_grid", "0001_initial"),
    ]

    operations = [migrations.RunPython(delete_retired_edges, migrations.RunPython.noop)]
