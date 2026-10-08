"""Delete `computing_core__user` rows: the type is retired (computing-core#27, highbar Q160).

`user` meant "a human who interacts with computing systems", which is `identity_core__human`.
It is removed, not redefined: an account on a host is the new `os_user`. computing_core never
emitted `user` itself, but samsite seeded three, so a grid upgraded in place still carries them.
With the model gone they would be spine rows of a type nothing defines; this removes each
`user` entity, its typed row, every edge that starts or ends at one, and each such edge's own
spine row. 0008 then drops the table.

Same shape as tap_web 0003_drop_landing_page. Direct ORM access is the sanctioned path in
migrations.
"""

from typing import Any

from django.db import migrations
from django.db.models import Q

RETIRED_ENTITY_TYPE = "computing_core__user"


def delete_user_rows(apps: Any, schema_editor: Any) -> None:
    Edge = apps.get_model("tap_grid", "Edge")
    Entity = apps.get_model("tap_grid", "Entity")
    users = Entity.objects.filter(entity_type=RETIRED_ENTITY_TYPE)
    # Edge rows cascade off their endpoint entities, but each edge's OWN spine row
    # (entity_type="edge") would be orphaned, so take those explicitly first.
    edges = Edge.objects.filter(Q(from_entity__in=users) | Q(to_entity__in=users))
    edge_entity_ids = list(edges.values_list("entity_id", flat=True))
    edges.delete()
    Entity.objects.filter(pk__in=edge_entity_ids).delete()
    users.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("computing_core", "0006_host_os_user_os_group"),
        ("tap_grid", "0001_initial"),
    ]

    operations = [migrations.RunPython(delete_user_rows, migrations.RunPython.noop)]
