"""Drop the retired `computing_core__user` table and its history table (computing-core#27).

Rows were removed by 0007_retire_user_rows; schema and data changes live in separate files.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("computing_core", "0007_retire_user_rows"),
    ]

    operations = [
        migrations.DeleteModel(name="HistoricalUser"),
        migrations.DeleteModel(name="User"),
    ]
