"""An IPv4-mapped IPv6 address is the IPv4 address (req-computing-core-ip-7, req-computing-core-ports-7).

``::ffff:10.0.0.5`` and ``10.0.0.5`` name one endpoint. ``address`` on ``ip_address`` and on
``port`` is a ``GenericIPAddressField(unpack_ipv4=True)``, so the field's own conversion stores
and keys the IPv4 form, whichever spelling an observer sent. Without it the two spellings are two
nodes, and two scanners that report the same host differently never meet.
"""

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration
from tap_plugin.computing_core.key_dimensions import NETWORK_NAME_ENTRY

from tap_grid.models import Entity
from tap_grid.registry import get_model_class
from tap_plugin.computing_core.tests.conftest import create_node

IP, PORT = "computing_core__ip_address", "computing_core__port"
MAPPED, PLAIN = "::ffff:10.0.0.5", "10.0.0.5"

pytestmark = pytest.mark.django_db


def _row(type_slug: str, payload: dict):
    result = create_node(type_slug, payload)
    assert result.success, result.errors
    return get_model_class(type_slug).objects.get(entity=Entity.objects.get(pk=result.entity_id))


@pytest.mark.spec("req-computing-core-ip-7")
class TestIpAddress:
    def test_the_mapped_spelling_is_stored_as_ipv4(self) -> None:
        assert _row(IP, {"network_name": "corp", "address": MAPPED}).address == PLAIN

    def test_either_spelling_finds_the_one_node(self) -> None:
        row = _row(IP, {"network_name": "corp", "address": PLAIN})
        model = get_model_class(IP)
        for spelling in (PLAIN, MAPPED):
            found = model.find_existing(**{NETWORK_NAME_ENTRY: "corp", "address": spelling})
            assert found is not None and found.pk == row.pk, spelling

    def test_a_real_ipv6_address_is_unchanged(self) -> None:
        assert _row(IP, {"network_name": "corp", "address": "2001:db8::5"}).address == "2001:db8::5"

    def test_a_mapped_loopback_is_still_refused(self) -> None:
        assert not create_node(IP, {"network_name": "corp", "address": "::ffff:127.0.0.1"}).success


@pytest.mark.spec("req-computing-core-ports-7")
class TestPort:
    def test_the_mapped_spelling_is_stored_as_ipv4_and_found_by_either(self) -> None:
        row = _row(PORT, {"network_name": "corp", "address": MAPPED, "transport": "tcp", "port_number": 443})
        assert row.address == PLAIN
        model = get_model_class(PORT)
        for spelling in (PLAIN, MAPPED):
            key = {NETWORK_NAME_ENTRY: "corp", "address": spelling, "transport": "tcp", "port_number": 443}
            found = model.find_existing(**key)
            assert found is not None and found.pk == row.pk, spelling


@pytest.mark.spec("req-computing-core-ip-7")
class TestTheUpgradeGuard:
    """0021 refuses while a stored row keeps the mapped spelling, which neither spelling would find."""

    def _guard(self):
        import importlib  # noqa: PLC0415

        return importlib.import_module("tap_plugin.computing_core.migrations.0021_unpack_ipv4_mapped").refuse_mapped_rows

    @pytest.mark.parametrize("type_slug", [IP, PORT])
    def test_a_stored_mapped_spelling_refuses_the_migration(self, type_slug) -> None:
        from django.apps import apps  # noqa: PLC0415
        from django.db import connection  # noqa: PLC0415

        payload = {"network_name": "corp", "address": PLAIN}
        if type_slug == PORT:
            payload |= {"transport": "tcp", "port_number": 443}
        row = _row(type_slug, payload)
        from psycopg import sql  # noqa: PLC0415

        statement = sql.SQL("UPDATE {} SET address = %s WHERE id = %s").format(sql.Identifier(row._meta.db_table))
        with connection.cursor() as cursor:  # written as a pre-0021 row would hold it
            cursor.execute(statement, [MAPPED, row.pk])
        with pytest.raises(RuntimeError, match="reload the data"):
            self._guard()(apps, None)

    def test_plain_rows_pass(self) -> None:
        from django.apps import apps  # noqa: PLC0415

        _row(IP, {"network_name": "corp", "address": PLAIN})
        self._guard()(apps, None)
