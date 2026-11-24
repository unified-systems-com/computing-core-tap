"""``ip_address`` and ``port`` are keyed per network (req-computing-core-ip-6, req-computing-core-ports-5).

The network is ``tap.computing.network_name``, an identity dimension stamped on the envelope
(form 3, unified-systems-com/tap#1355): ``Internet`` for every public address, the operator-declared
network name for a private one. The same private address in two networks is two nodes.
"""

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration
from tap_plugin.computing_core.key_dimensions import NETWORK_NAME_ENTRY

from tap_grid.registry import get_model_class
from tap_plugin.computing_core.tests.conftest import create_node

IP, PORT = "computing_core__ip_address", "computing_core__port"

pytestmark = pytest.mark.django_db


def _id(result) -> str:
    assert result.success, result.errors
    return str(result.entity_id)


@pytest.mark.spec("req-computing-core-ip-6")
class TestIpAddress:
    def test_the_key_is_network_then_address(self) -> None:
        assert get_model_class(IP).NATURAL_KEY == (NETWORK_NAME_ENTRY, "address")

    def test_one_private_address_in_two_networks_is_two_nodes(self) -> None:
        a = _id(create_node(IP, {"network_name": "vpc-a", "address": "10.0.0.5"}))
        b = _id(create_node(IP, {"network_name": "vpc-b", "address": "10.0.0.5"}))
        assert a != b
        found = get_model_class(IP).find_existing(**{NETWORK_NAME_ENTRY: "vpc-a", "address": "10.0.0.5"})
        assert str(found.entity_id) == a

    def test_the_network_is_required(self) -> None:
        assert not create_node(IP, {"address": "10.0.0.5"}).success


@pytest.mark.spec("req-computing-core-ports-5")
class TestPort:
    PAYLOAD = {"network_name": "Internet", "address": "203.0.113.7", "transport": "tcp", "port_number": 443}

    def test_the_key_is_network_address_transport_number(self) -> None:
        assert get_model_class(PORT).NATURAL_KEY == (NETWORK_NAME_ENTRY, "address", "transport", "port_number")
        assert "state" not in get_model_class(PORT).NATURAL_KEY

    def test_found_again_and_state_is_outside_the_key(self) -> None:
        entity_id = _id(create_node(PORT, {**self.PAYLOAD, "state": "listening"}))
        key = {NETWORK_NAME_ENTRY: "Internet", "address": "203.0.113.7", "transport": "tcp", "port_number": 443}
        assert str(get_model_class(PORT).find_existing(**key).entity_id) == entity_id

    @pytest.mark.parametrize("missing", ["network_name", "address", "port_number"])
    def test_key_fields_required(self, missing: str) -> None:
        payload = {k: v for k, v in self.PAYLOAD.items() if k != missing}
        assert not create_node(PORT, payload).success

    def test_a_null_port_number_cannot_be_keyed(self) -> None:
        assert not create_node(PORT, {**self.PAYLOAD, "port_number": None}).success

    @pytest.mark.parametrize("address", ["127.0.0.1", "::1", "0.0.0.0", "::", "169.254.10.1", "fe80::1"])
    def test_a_host_scoped_address_is_refused(self, address: str) -> None:
        assert not create_node(PORT, {**self.PAYLOAD, "address": address}).success


@pytest.mark.spec("req-computing-core-ports-6")
class TestAvailableAt:
    """A port is reachable at its address; the address is a reference and outlives the port."""

    def _pair(self):
        from tap_grid.models import Entity

        ip = Entity.objects.get(pk=_id(create_node(IP, {"network_name": "vpc-a", "address": "10.0.0.5"})))
        port = Entity.objects.get(pk=_id(create_node(PORT, {"network_name": "vpc-a", "address": "10.0.0.5", "transport": "tcp", "port_number": 22})))
        return ip, port

    def test_a_port_is_drawn_to_its_address(self) -> None:
        from tap_grid.models import Edge
        from tap_grid.services import create_edge

        ip, port = self._pair()
        edge = create_edge(port, ip, "AVAILABLE_AT__computing_core")
        assert Edge.objects.filter(pk=edge.pk, from_entity_id=port.id, to_entity_id=ip.id).exists()

    def test_the_address_outlives_the_port(self) -> None:
        from tap_grid.services import create_edge, delete_node

        ip, port = self._pair()
        create_edge(port, ip, "AVAILABLE_AT__computing_core")
        assert delete_node(port.id, cascade="contained").success
        ip.refresh_from_db()
        assert ip.deleted_at is None
