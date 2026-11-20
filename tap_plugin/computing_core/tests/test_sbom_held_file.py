"""An SBOM document as the format record of a held file, with the file store optional.

Spec: specs/spec-computing-core-v0.md (req-computing-core-file-format-record, req-computing-core-file-held-as).
Ruled 2026-11-19 in tap: computing-core does not require the file store. The pure library takes the
entity id of the ``tap_file`` a caller held the bytes in, or nothing; with nothing the document is
recorded the same and no ``FILE_CONTENTS`` edge is written.
"""

import io
import json
import tomllib
import uuid
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration
from django.core.exceptions import ValidationError
from tap_plugin.computing_core.sbom import (
    FILE_CONTENTS,
    SbomBatch,
    SbomParseError,
    Verification,
    parse_cyclonedx,
    record_document,
    record_parse_failure,
)

from tap_grid.exceptions import InvalidEdgeError
from tap_grid.grift import grift_import
from tap_grid.models import Edge, Entity
from tap_grid.registry import get_model_class
from tap_grid.services import create_edge, create_node

SPEC = pytest.mark.spec
VERIFIED = Verification("verified", signer="ci@example.org")
SOURCE = Verification("source-authenticated", source="registry.example.org")
REFUSED = Verification("refused", check="signer-identity")
UNOBSERVABLE = Verification("not-observable", check="no attestation")
PLUGIN = Path(__file__).resolve().parents[1]
CORPUS = PLUGIN / "tests" / "corpus" / "tap-web-latest-arm64.cdx.json"


def _document(batch: SbomBatch) -> dict:
    (row,) = batch.nodes_of("computing_core__sbom_document")
    return dict(row.properties)


def _import(batch: SbomBatch) -> None:
    document = {
        "metadata": {"grift_version": "0"},
        "_reserved": {},
        "batches": [batch.as_grift_batch(str(uuid.uuid4()), name="sbom held-file test", source="test")],
    }
    result = grift_import(document)
    assert result.success, [e.message for e in result.errors[:5]]


def _host() -> str:
    result = create_node("computing_core__host", {"realm": "assert", "stable_id": "held-file", "kind": "container"})
    assert result.success, result.errors
    return str(result.entity_id)


def _new_doc(**fields):
    model = get_model_class("computing_core__sbom_document")
    return model(content_digest="a" * 64, **fields)


# --------------------------------------------------------------------------- the pure library


class TestTheStoreIsOptional:
    @SPEC("req-computing-core-file-format-record-8")
    def test_no_held_file_means_no_edge(self):
        batch = parse_cyclonedx(CORPUS.read_bytes(), host_id=str(uuid.uuid4()), verification=VERIFIED)
        assert batch.edges_of(FILE_CONTENTS) == ()
        assert _document(batch)["parse_status"] == "valid" and _document(batch)["parse_note"] == ""

    @SPEC("req-computing-core-file-format-record-3")
    def test_a_held_file_is_joined_by_its_digest(self):
        held = str(uuid.uuid4())
        batch = parse_cyclonedx(CORPUS.read_bytes(), host_id=str(uuid.uuid4()), verification=VERIFIED, held_file_id=held)
        (edge,) = batch.edges_of(FILE_CONTENTS)
        (row,) = batch.nodes_of("computing_core__sbom_document")
        assert (edge.from_entity_id, edge.to_ref) == (held, row.ref)
        assert edge.as_grift()["edge"]["properties"] == {"sha256": row.properties["content_digest"]}

    @SPEC("req-computing-core-file-format-record-8")
    @pytest.mark.parametrize("verification", [REFUSED, UNOBSERVABLE, SOURCE])
    def test_a_recorded_document_takes_an_optional_held_file_too(self, verification):
        data = CORPUS.read_bytes()
        assert record_document(data, verification=verification).edges == ()
        held = str(uuid.uuid4())
        batch = record_document(data, verification=verification, held_file_id=held)
        (edge,) = batch.edges
        assert edge.edge_type == FILE_CONTENTS and edge.from_entity_id == held
        assert _document(batch)["parse_status"] is None and _document(batch)["parse_note"] == ""

    @pytest.mark.parametrize("bad", ["not-a-uuid", 7, b"x" * 16])
    def test_a_held_file_id_that_is_not_an_entity_id_is_refused(self, bad):
        with pytest.raises(ValueError, match="held_file_id"):
            parse_cyclonedx(CORPUS.read_bytes(), host_id=str(uuid.uuid4()), verification=VERIFIED, held_file_id=bad)
        with pytest.raises(ValueError, match="held_file_id"):
            record_document(CORPUS.read_bytes(), verification=REFUSED, held_file_id=bad)

    @SPEC("req-computing-core-file-format-record-8")
    def test_the_plugin_does_not_require_the_store(self):
        manifest = tomllib.loads((PLUGIN / "tap-plugin.toml").read_text(encoding="utf-8"))
        assert "file_store" not in manifest


class TestParsingIsNotAuthentication:
    @SPEC("req-computing-core-file-format-record-4")
    def test_a_vouched_for_document_that_fails_to_parse_is_kept_invalid(self):
        body = b'{"bomFormat": "CycloneDX", "specVersion": "1.2"}'
        with pytest.raises(SbomParseError) as failed:
            parse_cyclonedx(body, host_id=str(uuid.uuid4()), verification=VERIFIED)
        batch = record_parse_failure(body, verification=VERIFIED, error=failed.value, held_file_id=str(uuid.uuid4()))
        row = _document(batch)
        assert row["parse_status"] == "invalid" and "1.2" in row["parse_note"]
        assert len(batch.edges_of(FILE_CONTENTS)) == 1 and len(batch.nodes) == 1

    @SPEC("req-computing-core-file-format-record-5")
    def test_signed_and_malformed_keeps_both_facts(self):
        row = _document(record_parse_failure(b"{not json", verification=VERIFIED, error="not JSON: line 1"))
        assert (row["verified"], row["signer"]) == (True, "ci@example.org")
        assert (row["parse_status"], row["parse_note"]) == ("invalid", "not JSON: line 1")

    @SPEC("req-computing-core-file-format-record-5")
    def test_a_source_authenticated_failure_keeps_its_source(self):
        row = _document(record_parse_failure(b"[]", verification=SOURCE, error="not a CycloneDX document"))
        assert row["verified"] is None and row["authenticated_source"] == "registry.example.org"
        assert row["parse_status"] == "invalid"

    @pytest.mark.parametrize("verification", [REFUSED, UNOBSERVABLE])
    def test_only_a_vouched_for_document_can_fail_to_parse(self, verification):
        with pytest.raises(ValueError):
            record_parse_failure(b"{}", verification=verification, error="x")

    def test_the_note_is_one_plain_line(self):
        row = _document(record_parse_failure(b"{}", verification=VERIFIED, error="line one\nline\ttwo" + "x" * 400))
        assert "\n" not in row["parse_note"] and "\t" not in row["parse_note"] and len(row["parse_note"]) <= 255


# --------------------------------------------------------------------------- the model


@pytest.mark.django_db
class TestParseOutcomeIsStrict:
    @SPEC("req-computing-core-file-format-record-6")
    @pytest.mark.parametrize(
        ("fields", "ok"),
        [
            ({"verified": True, "signer": "s", "parse_status": "valid"}, True),
            ({"verified": True, "signer": "s", "parse_status": "invalid", "parse_note": "bad"}, True),
            ({"verified": True, "signer": "s", "parse_status": None}, True),
            ({"verified": None, "authenticated_source": "r", "parse_status": "valid"}, True),
            ({"verified": True, "signer": "s", "parse_status": "invalid"}, False),
            ({"verified": True, "signer": "s", "parse_status": "valid", "parse_note": "x"}, False),
            ({"verified": True, "signer": "s", "parse_status": "maybe"}, False),
            ({"verified": False, "verification_note": "signer-identity", "parse_status": "valid"}, False),
            ({"verified": None, "verification_note": "no attestation", "parse_status": "invalid", "parse_note": "x"}, False),
            ({"verified": None, "parse_status": None, "parse_note": "x"}, False),
        ],
    )
    def test_the_outcome_table(self, fields, ok):
        doc = _new_doc(**fields)
        if ok:
            doc.validate()
        else:
            with pytest.raises(ValidationError):
                doc.validate()


# --------------------------------------------------------------------------- on the grid


@pytest.fixture
def store(tmp_path, settings):
    from tap_files.store.local import LocalBackend

    root = tmp_path / "files"
    root.mkdir()
    LocalBackend(root).initialise()
    settings.TAP_FILES_ROOT = str(root)
    return root


def _hold(data: bytes):
    from tap_files.holding import hold_file

    return hold_file(f"/sboms/{uuid.uuid4().hex}.cdx.json", io.BytesIO(data), media_type="application/vnd.cyclonedx+json")


@pytest.mark.django_db
class TestOnTheGrid:
    @SPEC("req-computing-core-file-format-record-8")
    def test_with_no_store_the_document_lands_and_nothing_else(self, settings):
        settings.TAP_FILES_ROOT = ""
        _import(parse_cyclonedx(CORPUS.read_bytes(), host_id=_host(), verification=VERIFIED))
        doc = get_model_class("computing_core__sbom_document").objects.get()
        assert doc.parse_status == "valid"
        assert not Edge.objects.filter(edge_type=FILE_CONTENTS).exists()
        assert not get_model_class("tap_file").objects.exists()

    @SPEC("req-computing-core-file-format-record-3")
    def test_a_held_sbom_is_joined_to_its_record(self, store):
        data = CORPUS.read_bytes()
        held = _hold(data)
        _import(parse_cyclonedx(data, host_id=_host(), verification=VERIFIED, held_file_id=str(held.entity_id)))
        doc = get_model_class("computing_core__sbom_document").objects.get()
        (edge,) = Edge.objects.filter(edge_type=FILE_CONTENTS)
        assert (edge.from_entity_id, edge.to_entity_id) == (held.entity_id, doc.entity_id)
        assert edge.properties["sha256"] == held.sha256 == doc.content_digest

    @SPEC("req-computing-core-file-format-record-4")
    def test_an_invalid_held_document_is_kept(self, store):
        body = json.dumps({"bomFormat": "CycloneDX", "specVersion": "1.2"}).encode()
        held = _hold(body)
        try:
            parse_cyclonedx(body, host_id=_host(), verification=VERIFIED)
            raise AssertionError("1.2 must not parse")
        except SbomParseError as exc:
            _import(record_parse_failure(body, verification=VERIFIED, error=exc, held_file_id=str(held.entity_id)))
        doc = get_model_class("computing_core__sbom_document").objects.get()
        assert doc.parse_status == "invalid" and doc.parse_note and doc.verified is True
        assert Edge.objects.filter(edge_type=FILE_CONTENTS, to_entity_id=doc.entity_id).count() == 1


@pytest.mark.django_db
class TestHeldAs:
    @SPEC("req-computing-core-file-held-as-1")
    def test_a_host_file_links_to_its_held_copy(self, store):
        held = _hold(b"a config file")
        observed = create_node("computing_core__file", {"name": "app.conf", "file_path": "/etc/app.conf"})
        assert observed.success, observed.errors
        edge = create_edge(
            Entity.objects.get(pk=observed.entity_id), Entity.objects.get(pk=held.entity_id), "HELD_AS__computing_core", {}
        )
        assert edge.from_entity_id == observed.entity_id and edge.to_entity_id == held.entity_id

    @SPEC("req-computing-core-file-held-as-1")
    def test_only_a_host_file_to_a_tap_file(self, store):
        held = _hold(b"x")
        stranger = create_node("computing_core__host", {"realm": "assert", "stable_id": "h2", "kind": "container"})
        observed = create_node("computing_core__file", {"name": "a", "file_path": "/a"})
        with pytest.raises(InvalidEdgeError):
            create_edge(Entity.objects.get(pk=stranger.entity_id), Entity.objects.get(pk=held.entity_id), "HELD_AS__computing_core", {})
        with pytest.raises(InvalidEdgeError):
            create_edge(Entity.objects.get(pk=observed.entity_id), Entity.objects.get(pk=stranger.entity_id), "HELD_AS__computing_core", {})
