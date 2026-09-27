"""The neutral host and its two edges (req-computing-core-host, req-computing-core-host-edges).

Service-layer creation, the closed vocabularies, three-state fields, identity, display projection,
dimensions, and that ASSIGNED_TO_HUMAN / REPRESENTS_HOST connect their declared endpoints and refuse
properties their schemas do not name.
"""

import json
import tomllib
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration
from tap_plugin.computing_core.models.host import FORM_FACTORS, Host

from tap_grid.caller_context import CallerContext
from tap_grid.models import Edge, Entity
from tap_grid.services import WriteOperation, create_node, write_batch

PKG = Path(__file__).resolve().parents[1]
MANIFEST = tomllib.loads((PKG / "tap-plugin.toml").read_text())
HOST = "computing_core__host"
HUMAN = "identity_core__human"
ASSIGNED = "ASSIGNED_TO_HUMAN__computing_core"
REPRESENTS = "REPRESENTS_HOST__computing_core"


def _node(type_slug: str, payload: dict) -> str:
    result = create_node(type_slug, payload)
    assert result.success, f"create_node failed: {result.errors}"
    return str(result.entity_id)


def _host(entity_id: str) -> Host:
    return Host.objects.get(entity_id=entity_id)


def _edge(src: str, dst: str, edge_type: str, properties: dict | None = None):
    payload = {"properties": properties} if properties is not None else {}
    return write_batch(
        [WriteOperation(verb="create_edge", from_target=src, to_target=dst, edge_type=edge_type, payload=payload)],
        caller_context=CallerContext(),
    ).results[0]


@pytest.mark.django_db
class TestHostModel:
    def test_create_with_every_field(self):
        host = _host(
            _node(
                HOST,
                {
                    "asset_tag": "A-01234",
                    "name": "gc-mbp",
                    "form_factor": "laptop",
                    "os": "macOS 15.6",
                    "managed": True,
                    "ownership": "corporate",
                },
            )
        )
        assert (host.form_factor, host.os, host.managed, host.ownership) == ("laptop", "macOS 15.6", True, "corporate")

    def test_asset_tag_is_required(self):
        assert not create_node(HOST, {"name": "no tag"}).success

    def test_unobserved_fields_stay_unobserved(self):
        """req-computing-core-host-3: blank / null mean not observed, never a default that reads as a finding."""
        host = _host(_node(HOST, {"asset_tag": "A-2"}))
        assert (host.form_factor, host.ownership, host.os) == ("", "", "")
        assert host.managed is None

    def test_observed_unmanaged_is_false_not_null(self):
        assert _host(_node(HOST, {"asset_tag": "A-3", "managed": False})).managed is False

    @pytest.mark.parametrize("value", [v for v in FORM_FACTORS if v])
    def test_every_form_factor_is_accepted(self, value):
        assert create_node(HOST, {"asset_tag": f"ff-{value}", "form_factor": value}).success

    @pytest.mark.parametrize(
        ("field", "value"),
        [("form_factor", "workstation"), ("form_factor", "ephemeral_runner"), ("ownership", "byod")],
    )
    def test_closed_vocabularies_refuse_other_values(self, field, value):
        assert not create_node(HOST, {"asset_tag": "A-4", field: value}).success

    def test_no_free_form_record(self):
        assert not create_node(HOST, {"asset_tag": "A-5", "configuration": {"serial": "C02X"}}).success

    def test_identity_is_the_asset_tag(self):
        """req-computing-core-host-2: the key survives a rename."""
        assert Host.NATURAL_KEY == ("asset_tag",)
        host = _host(_node(HOST, {"asset_tag": "A-6", "name": "old-name"}))
        host.name = "new-name"
        host.save()
        # The key is a column, so a rename leaves the row found by it. (Queried directly rather than
        # through BaseModel.find_existing, which the plugin's requires_tap floor predates.)
        assert list(Host.objects.filter(asset_tag="A-6").values_list("pk", flat=True)) == [host.pk]

    def test_display_name_falls_back_to_asset_tag(self):
        named = _host(_node(HOST, {"asset_tag": "A-7", "name": "build-01"}))
        bare = _host(_node(HOST, {"asset_tag": "A-8"}))
        assert Entity.objects.get(pk=named.entity_id).name == "build-01"
        assert Entity.objects.get(pk=bare.entity_id).name == "A-8"

    def test_default_dimension(self):
        host = _host(_node(HOST, {"asset_tag": "A-9"}))
        assert Entity.objects.get(pk=host.entity_id).dimensions.get("tap.computing") == "host"


@pytest.mark.parametrize(
    ("slug", "sources", "targets"),
    [("ASSIGNED_TO_HUMAN", [HOST], [HUMAN]), ("REPRESENTS_HOST", None, [HOST])],
)
def test_edge_endpoints_are_declared(slug, sources, targets):
    """req-computing-core-host-edges: the endpoint lists the edge files carry.

    Enforcement is the grid's permission union (req-grid-edge-constraints-3): a node type declaring no
    OUTBOUND_EDGES / INBOUND_EDGES is unconstrained on that side, so a refusal cannot be proven from
    the undeclared types here; the declaration is what this plugin owns and what is asserted.
    """
    definition = json.loads((PKG / "edges" / f"{slug}.edge.json").read_text())
    assert MANIFEST["edges"][f"{slug}__computing_core"] == f"edges/{slug}.edge.json"
    assert definition.get("sources") == sources
    assert definition["targets"] == targets
    assert definition["property_schema"]["additionalProperties"] is False


def test_identity_core_is_the_declared_vocabulary_dependency():
    """req-computing-core-host-edges-1: the one foreign type named is identity_core's, and it is declared."""
    assert {d["slug"]: d.get("min_version") for d in MANIFEST["depends_on"]} == {"identity_core": "0.1.3"}


@pytest.mark.django_db
class TestAssignedToHuman:
    def test_host_is_assigned_to_a_human(self):
        host = _node(HOST, {"asset_tag": "A-10", "form_factor": "laptop"})
        human = _node(HUMAN, {"handle": "t-0001", "name": "Test Person"})
        result = _edge(host, human, ASSIGNED)
        assert result.success, result
        edge = Edge.objects.get(entity_id=result.entity_id)
        assert Entity.objects.get(pk=edge.entity_id).dimensions.get("tap.computing") == "identity"

    def test_a_shared_host_keeps_both_assignments(self):
        kiosk = _node(HOST, {"asset_tag": "A-11", "form_factor": "tablet"})
        first, second = _node(HUMAN, {"handle": "t-0002"}), _node(HUMAN, {"handle": "t-0003"})
        assert _edge(kiosk, first, ASSIGNED).success
        assert _edge(kiosk, second, ASSIGNED).success
        assert Edge.objects.filter(from_entity_id=kiosk, edge_type=ASSIGNED).count() == 2

    def test_carries_no_properties(self):
        host = _node(HOST, {"asset_tag": "A-14"})
        human = _node(HUMAN, {"handle": "t-0005"})
        assert not _edge(host, human, ASSIGNED, {"assigned_by": "mdm"}).success


@pytest.mark.django_db
class TestRepresentsHost:
    def test_any_record_can_represent_a_host(self):
        """Wildcard source: a file node stands in for a vendor device record, which computing_core cannot name."""
        host = _node(HOST, {"asset_tag": "A-20"})
        record = _node("computing_core__file", {"file_path": "/var/db/device-record"})
        result = _edge(record, host, REPRESENTS, {"matched_on": "serial number"})
        assert result.success, result
        edge = Edge.objects.get(entity_id=result.entity_id)
        assert edge.properties == {"matched_on": "serial number"}
        assert Entity.objects.get(pk=edge.entity_id).dimensions.get("tap.computing") == "host"

    def test_unknown_property_is_refused(self):
        host = _node(HOST, {"asset_tag": "A-21"})
        record = _node("computing_core__file", {"file_path": "/var/db/r2"})
        refused = _edge(record, host, REPRESENTS, {"matched_by": "hostname"})
        assert not refused.success
        assert "matched_by" in " ".join(str(e) for e in refused.errors)
