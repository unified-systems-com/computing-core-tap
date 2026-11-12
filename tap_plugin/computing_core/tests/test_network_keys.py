"""`ip_address` and `port` are found by the network they are on (req-computing-core-ip-4,
req-computing-core-ports-5).

An address means one thing only inside its address space, so both types key on `network_name`
first: `Internet` for every public address, the operator-declared name for a private one.
"""

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration

from tap_grid.models import Entity, natural_key_index_name
from tap_grid.registry import get_model_class
from tap_grid.services import create_node

IP = {"network_name": "corp", "address": "10.0.1.5", "version": 4}
PORT = {"network_name": "corp", "address": "10.0.1.5", "transport": "tcp", "port_number": 443}


def _create(type_slug: str, payload: dict):
    result = create_node(type_slug, payload)
    assert result.success, f"create_node failed: {result.errors}"
    return get_model_class(type_slug).objects.get(entity=Entity.objects.get(pk=result.entity_id))


class TestDeclarations:
    def test_ip_address_key(self):
        assert get_model_class("computing_core__ip_address").NATURAL_KEY == ("network_name", "address")

    def test_port_key(self):
        assert get_model_class("computing_core__port").NATURAL_KEY == (
            "network_name",
            "address",
            "transport",
            "port_number",
        )

    @pytest.mark.parametrize(
        ("type_slug", "fields"),
        [
            ("computing_core__ip_address", ["network_name", "address"]),
            ("computing_core__port", ["network_name", "address", "transport", "port_number"]),
        ],
    )
    def test_key_is_indexed_in_declared_order(self, type_slug, fields):
        model = get_model_class(type_slug)
        name = natural_key_index_name(model._meta.db_table)
        index = next(i for i in model._meta.indexes if i.name == name)
        assert list(index.fields) == fields

    @pytest.mark.parametrize(
        ("type_slug", "required"),
        [
            ("computing_core__ip_address", ["network_name", "address"]),
            ("computing_core__port", ["network_name", "address", "transport", "port_number"]),
        ],
    )
    def test_key_fields_are_required_and_declared_in_both_schemas(self, type_slug, required):
        model = get_model_class(type_slug)
        for field in required:
            assert field in model.CREATE_REQUIRED
            assert field in model.FIELD_CRUD_SCHEMA
            assert field in model.FIELD_VALIDATION_SCHEMA
            assert not model._meta.get_field(field).null

    def test_port_state_stays_outside_the_key(self):
        model = get_model_class("computing_core__port")
        assert "state" not in model.NATURAL_KEY
        assert "state" in {f.name for f in model._meta.get_fields()}


@pytest.mark.django_db
class TestIpAddress:
    def test_found_again_by_network_and_address(self):
        node = _create("computing_core__ip_address", IP)
        model = get_model_class("computing_core__ip_address")
        assert model.find_existing(network_name="corp", address="10.0.1.5").pk == node.pk
        assert model.find_existing(network_name="lab", address="10.0.1.5") is None

    def test_one_private_address_on_two_networks_is_two_nodes(self):
        a = _create("computing_core__ip_address", IP)
        b = _create("computing_core__ip_address", {**IP, "network_name": "lab"})
        assert a.pk != b.pk

    def test_public_address_lives_on_the_internet_network(self):
        node = _create("computing_core__ip_address", {"network_name": "Internet", "address": "203.0.113.7"})
        model = get_model_class("computing_core__ip_address")
        assert model.find_existing(network_name="Internet", address="203.0.113.7").pk == node.pk

    @pytest.mark.parametrize("missing", ["network_name", "address"])
    def test_key_fields_required(self, missing):
        payload = {k: v for k, v in IP.items() if k != missing}
        assert not create_node("computing_core__ip_address", payload).success

    def test_blank_network_is_refused(self):
        assert not create_node("computing_core__ip_address", {**IP, "network_name": ""}).success


@pytest.mark.django_db
class TestPort:
    def test_found_again_by_network_address_transport_and_number(self):
        node = _create("computing_core__port", PORT)
        model = get_model_class("computing_core__port")
        assert model.find_existing(**PORT).pk == node.pk
        assert model.find_existing(**{**PORT, "port_number": 80}) is None
        assert model.find_existing(**{**PORT, "transport": "udp"}) is None
        assert model.find_existing(**{**PORT, "address": "10.0.1.50"}) is None
        assert model.find_existing(**{**PORT, "network_name": "lab"}) is None

    def test_same_number_at_two_addresses_is_two_ports(self):
        a = _create("computing_core__port", PORT)
        b = _create("computing_core__port", {**PORT, "address": "10.0.1.6"})
        assert a.pk != b.pk

    @pytest.mark.parametrize("missing", ["network_name", "address", "port_number"])
    def test_key_fields_required(self, missing):
        payload = {k: v for k, v in PORT.items() if k != missing}
        assert not create_node("computing_core__port", payload).success

    def test_display_name(self):
        node = _create("computing_core__port", PORT)
        assert node.get_name() == "10.0.1.5:443/tcp"
        v6 = _create("computing_core__port", {**PORT, "address": "fe80::1"})
        assert v6.get_name() == "[fe80::1]:443/tcp"
