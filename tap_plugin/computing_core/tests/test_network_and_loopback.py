"""Tests for `network`, `loopback_address`, `DEFINES_LOOPBACK_ADDRESS`, and what `ip_address` refuses.

req-computing-core-network, req-computing-core-loopback and req-computing-core-ip-4: creation
through the service layer, the declared natural keys (found again by the generated search), a
network's name fixed once written, ranges validated and stored canonically, a loopback address
keyed to its host and retired with it, and loopback, wildcard and link-local addresses refused
on `ip_address`.
"""

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration
from tap_plugin.computing_core.addresses import LINK_LOCAL, LOOPBACK, WILDCARD, host_scoped_kind
from tap_plugin.computing_core.models.network import normalise_ranges

from tap_grid.constraints import InvalidEdgeError
from tap_grid.models import Edge, Entity
from tap_grid.registry import get_model_class
from tap_grid.services import create_edge, create_node, delete_node, patch_node

HOST = {"realm": "machine-id", "stable_id": "4c4c4544-0042-3510-8051-b4c04f4b4e31", "name": "build-01"}
OTHER_HOST = {"realm": "machine-id", "stable_id": "9f1e2d3c-0000-4000-8000-000000000001", "name": "build-02"}


def _on(host: dict) -> dict:
    return {"host_realm": host["realm"], "host_stable_id": host["stable_id"]}


def _create(type_slug: str, payload: dict):
    """Create a node via the service layer and return the typed domain object."""
    result = create_node(type_slug, payload)
    assert result.success, f"create_node failed: {result.errors}"
    return get_model_class(type_slug).objects.get(entity=Entity.objects.get(pk=result.entity_id))


def _errors(result) -> str:
    return " ".join(str(e) for e in result.errors)


class TestAddressClassification:
    """The pure classifier both address types use (no database)."""

    @pytest.mark.parametrize(
        ("value", "kind"),
        [
            ("127.0.0.1", LOOPBACK),
            ("127.42.0.9", LOOPBACK),
            ("::1", LOOPBACK),
            ("::ffff:127.0.0.1", LOOPBACK),
            ("0.0.0.0", WILDCARD),
            ("::", WILDCARD),
            ("169.254.169.254", LINK_LOCAL),
            ("fe80::1", LINK_LOCAL),
            ("10.0.0.5", None),
            ("203.0.113.7", None),
            ("2001:db8::5", None),
            ("::ffff:10.0.0.5", None),
        ],
    )
    def test_kind(self, value, kind):
        assert host_scoped_kind(value) == kind

    def test_not_an_address(self):
        with pytest.raises(ValueError):
            host_scoped_kind("not-an-ip")


@pytest.mark.django_db
class TestIpAddressRefusals:
    @pytest.mark.parametrize("address", ["10.0.0.5", "203.0.113.7", "2001:db8::5"])
    def test_shareable_addresses_accepted(self, address):
        assert create_node("computing_core__ip_address", {"address": address}).success

    @pytest.mark.parametrize("address", ["127.0.0.1", "::1", "::ffff:127.0.0.1"])
    def test_loopback_refused_and_pointed_at_loopback_address(self, address):
        result = create_node("computing_core__ip_address", {"address": address})
        assert not result.success
        assert "computing_core__loopback_address" in _errors(result)

    @pytest.mark.parametrize("address", ["0.0.0.0", "::"])
    def test_wildcard_refused(self, address):
        result = create_node("computing_core__ip_address", {"address": address})
        assert not result.success
        assert "wildcard" in _errors(result)

    @pytest.mark.parametrize("address", ["169.254.169.254", "fe80::1"])
    def test_link_local_refused(self, address):
        result = create_node("computing_core__ip_address", {"address": address})
        assert not result.success
        assert "link-local" in _errors(result)


class TestNormaliseRanges:
    """The pure range normaliser (no database)."""

    def test_canonical_sorted_and_deduplicated(self):
        assert normalise_ranges(["10.1.0.0/16", "2001:DB8::/32", "10.0.0.0/16", "10.1.0.0/16"]) == [
            "10.0.0.0/16",
            "10.1.0.0/16",
            "2001:db8::/32",
        ]

    def test_host_bits_refused(self):
        with pytest.raises(ValueError):
            normalise_ranges(["10.0.0.1/8"])


@pytest.mark.django_db
class TestNetwork:
    def test_create_with_ranges_stored_canonically(self):
        node = _create(
            "computing_core__network",
            {"name": "corp", "description": "Corporate network", "ranges": ["10.1.0.0/16", "2001:DB8::/32", "10.0.0.0/16"]},
        )
        node.refresh_from_db()
        node.entity.refresh_from_db()
        assert node.ranges == ["10.0.0.0/16", "10.1.0.0/16", "2001:db8::/32"]
        assert node.entity.name == "corp"
        assert node.entity.dimensions.get("tap.computing") == "network"

    def test_ranges_may_be_unstated(self):
        node = _create("computing_core__network", {"name": "Internet"})
        assert node.ranges is None

    @pytest.mark.parametrize("ranges", [["10.0.0.1/8"], ["not-a-range"], ["10.0.0.0/33"], "10.0.0.0/8", [10]])
    def test_bad_ranges_refused(self, ranges):
        assert not create_node("computing_core__network", {"name": "corp", "ranges": ranges}).success

    def test_name_required(self):
        assert not create_node("computing_core__network", {"description": "no name"}).success
        assert not create_node("computing_core__network", {"name": "   "}).success

    def test_found_again_by_name(self):
        node = _create("computing_core__network", {"name": "vpc-0abc1234def567890"})
        model = get_model_class("computing_core__network")
        assert model.NATURAL_KEY == ("name",)
        assert model.objects.get(name="vpc-0abc1234def567890").pk == node.pk

    def test_name_fixed_once_written(self):
        node = _create("computing_core__network", {"name": "corp"})
        result = patch_node(node.entity_id, {"name": "corp-renamed"})
        assert not result.success
        assert "fixed once written" in _errors(result)
        node.refresh_from_db()
        assert node.name == "corp"

    def test_description_and_ranges_may_change(self):
        node = _create("computing_core__network", {"name": "corp", "ranges": ["10.0.0.0/16"]})
        result = patch_node(node.entity_id, {"description": "HQ", "ranges": ["10.0.0.0/8"]})
        assert result.success, result.errors
        node.refresh_from_db()
        assert (node.description, node.ranges) == ("HQ", ["10.0.0.0/8"])


@pytest.mark.django_db
class TestLoopbackAddress:
    def test_create_and_display(self):
        node = _create("computing_core__loopback_address", {**_on(HOST), "address": "127.0.0.1"})
        node.entity.refresh_from_db()
        assert node.entity.name == "127.0.0.1"
        assert node.entity.dimensions.get("tap.computing") == "network"

    @pytest.mark.parametrize("address", ["127.0.0.1", "127.0.1.1", "::1"])
    def test_loopback_accepted(self, address):
        assert create_node("computing_core__loopback_address", {**_on(HOST), "address": address}).success

    @pytest.mark.parametrize("address", ["10.0.0.5", "0.0.0.0", "fe80::1", "not-an-ip"])
    def test_non_loopback_refused(self, address):
        assert not create_node("computing_core__loopback_address", {**_on(HOST), "address": address}).success

    @pytest.mark.parametrize("missing", ["host_realm", "host_stable_id", "address"])
    def test_key_fields_required(self, missing):
        payload = {k: v for k, v in {**_on(HOST), "address": "127.0.0.1"}.items() if k != missing}
        assert not create_node("computing_core__loopback_address", payload).success

    def test_same_address_on_two_hosts_is_two_nodes(self):
        a = _create("computing_core__loopback_address", {**_on(HOST), "address": "127.0.0.1"})
        b = _create("computing_core__loopback_address", {**_on(OTHER_HOST), "address": "127.0.0.1"})
        assert a.pk != b.pk
        model = get_model_class("computing_core__loopback_address")
        assert model.NATURAL_KEY == ("host_realm", "host_stable_id", "address")
        assert model.objects.get(**_on(HOST), address="127.0.0.1").pk == a.pk


@pytest.mark.django_db
class TestDefinesLoopbackAddress:
    def test_host_to_loopback_only(self):
        host = _create("computing_core__host", HOST)
        lo = _create("computing_core__loopback_address", {**_on(HOST), "address": "127.0.0.1"})
        create_edge(host.entity, lo.entity, "DEFINES_LOOPBACK_ADDRESS__computing_core")
        # The host declares its inbound edges, so the reverse direction is refused.
        with pytest.raises(InvalidEdgeError):
            create_edge(lo.entity, host.entity, "DEFINES_LOOPBACK_ADDRESS__computing_core")
        # loopback_address declares its inbound edges, so a source other than a host is refused.
        user = _create("computing_core__os_user", {**_on(HOST), "local_id": "root"})
        with pytest.raises(InvalidEdgeError):
            create_edge(user.entity, lo.entity, "DEFINES_LOOPBACK_ADDRESS__computing_core")

    def test_loopback_retires_with_its_host(self):
        host = _create("computing_core__host", HOST)
        lo = _create("computing_core__loopback_address", {**_on(HOST), "address": "127.0.0.1"})
        edge = create_edge(host.entity, lo.entity, "DEFINES_LOOPBACK_ADDRESS__computing_core")
        assert delete_node(host.entity_id, cascade="contained").success
        lo.entity.refresh_from_db()
        assert lo.entity.deleted_at is not None
        assert Edge.objects.filter(pk=edge.pk, entity__deleted_at__isnull=True).count() == 0
