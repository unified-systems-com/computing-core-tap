"""Key `ip_address` on (network_name, address) and `port` on (network_name, address, transport,
port_number) (req-computing-core-ip-4, req-computing-core-ports-5).

Neither type had a declared natural key, and neither carried the network it is on, so an existing
row cannot be given one honestly: its network was never recorded, and a port row never recorded
its address at all. Rather than invent values, this migration refuses to run while any `ip_address`
or `port` row exists, live or historical, and names the counts. No collector in the fleet writes
either type yet, so a grid built from this plugin's own seeds has none. A grid that does must
remove them (or re-collect them under a source that supplies the network) before upgrading.

The temporary defaults below exist only because Django needs one to add a NOT NULL column; they are
not kept (`preserve_default=False`) and, with the tables checked empty, never land on a row.
"""

from typing import Any

from django.db import migrations, models

TABLES = ("IpAddress", "HistoricalIpAddress", "Port", "HistoricalPort")


def refuse_unkeyable_rows(apps: Any, schema_editor: Any) -> None:
    counts = {name: apps.get_model("computing_core", name)._base_manager.count() for name in TABLES}
    present = {name: n for name, n in counts.items() if n}
    if present:
        raise RuntimeError(
            "computing_core 0018 cannot key existing ip_address/port rows: they carry no network_name "
            f"(and port rows no address). Rows present: {present}. Remove them, or re-collect them "
            "with a source that supplies the network, then migrate again."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("computing_core", "0017_kubernetes_annotations"),
    ]

    operations = [
        migrations.RunPython(refuse_unkeyable_rows, migrations.RunPython.noop),
        migrations.AddField(
            model_name="ipaddress",
            name="network_name",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="historicalipaddress",
            name="network_name",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="port",
            name="network_name",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="historicalport",
            name="network_name",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="port",
            name="address",
            field=models.GenericIPAddressField(default="0.0.0.0"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="historicalport",
            name="address",
            field=models.GenericIPAddressField(default="0.0.0.0"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="port",
            name="port_number",
            field=models.PositiveIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalport",
            name="port_number",
            field=models.PositiveIntegerField(db_index=True),
        ),
        migrations.AddIndex(
            model_name="ipaddress",
            index=models.Index(fields=["network_name", "address"], name="nk_computing_core__ip_address"),
        ),
        migrations.AddIndex(
            model_name="port",
            index=models.Index(
                fields=["network_name", "address", "transport", "port_number"], name="nk_computing_core__port"
            ),
        ),
    ]
