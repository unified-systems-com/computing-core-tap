"""An unsigned SBOM from an authenticated source is parsed and never verified (req-computing-core-sbom-source-auth).

The outcome is the caller's claim: it fetched the bytes itself, from a system it authenticated to
with an operator-provisioned credential, over verified TLS. This module cannot see a transport;
it pins what the outcome does once claimed.
"""

import hashlib
import uuid
from pathlib import Path

import pytest
from tap_plugin.computing_core.sbom import Verification, parse_cyclonedx, parse_cyclonedx_vulnerabilities, record_document
from tap_plugin.computing_core.sbom.verification import SOURCE_AUTHENTICATED

import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration

from tap_grid.models import Entity
from tap_grid.registry import get_model_class
from tap_grid.services import create_node

CORPUS = Path(__file__).resolve().parent / "corpus" / "tap-web-latest-arm64.cdx.json"
HOST = str(uuid.UUID("01a13c38-4f5e-735c-9cf2-1f159f4282b6"))
TYPE = "computing_core__sbom_document"
SOURCE = '["https://anchore.example:8228/v2","acct"]'
FROM_SOURCE = Verification(SOURCE_AUTHENTICATED, source=SOURCE)
SUBJECT = "sha256:" + "a" * 64
SERIAL = "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79"


@pytest.fixture(scope="module")
def corpus_bytes() -> bytes:
    return CORPUS.read_bytes()


def row(batch):
    (document,) = batch.nodes_of(TYPE)
    return document.properties


class TestTheOutcome:
    def test_it_names_its_source_and_is_never_verified(self):
        assert FROM_SOURCE.verified is None
        assert FROM_SOURCE.document_fields() == {"verified": None, "signer": "", "verification_note": "", "authenticated_source": SOURCE}

    @pytest.mark.parametrize("source", ["", "   "])
    def test_a_source_is_required(self, source):
        with pytest.raises(ValueError, match="names the system"):
            Verification(SOURCE_AUTHENTICATED, source=source)

    @pytest.mark.parametrize("extra", [{"signer": "ci@example.org"}, {"check": "subject-digest"}])
    def test_it_carries_no_signer_and_no_failing_check(self, extra):
        with pytest.raises(ValueError, match="no signer and no failing check"):
            Verification(SOURCE_AUTHENTICATED, source=SOURCE, **extra)

    @pytest.mark.parametrize("outcome, fields", [("verified", {"signer": "ci"}), ("refused", {"check": "subject-digest"}), ("not-observable", {})])
    def test_no_other_outcome_takes_a_source(self, outcome, fields):
        with pytest.raises(ValueError, match="only a source-authenticated document records a source"):
            Verification(outcome, source=SOURCE, **fields)

    @pytest.mark.parametrize("source", ["a\nb", "a\x00b", "x" * 513, 7])
    def test_a_source_is_bounded_plain_text(self, source):
        with pytest.raises(ValueError):
            Verification(SOURCE_AUTHENTICATED, source=source)  # type: ignore[arg-type]


class TestParsedNeverVerified:
    def test_the_document_is_parsed_and_its_row_says_where_it_came_from(self, corpus_bytes):
        batch = parse_cyclonedx(corpus_bytes, host_id=HOST, verification=FROM_SOURCE)
        document = row(batch)
        assert (document["verified"], document["signer"], document["verification_note"], document["authenticated_source"]) == (None, "", "", SOURCE)
        assert document["content_digest"] == hashlib.sha256(corpus_bytes).hexdigest()
        # The same inventory a verified parse yields: the outcome changes the document row only.
        signed = parse_cyclonedx(corpus_bytes, host_id=HOST, verification=Verification("verified", signer="ci@example.org"))
        assert len(batch.nodes) == len(signed.nodes) and len(batch.edges) == len(signed.edges)
        assert len(batch.nodes_of("computing_core__package")) > 100

    @pytest.mark.parametrize("verification", [Verification("refused", "subject-digest"), Verification("not-observable")])
    def test_the_other_two_outcomes_are_still_refused_before_a_byte_is_read(self, verification, monkeypatch):
        import tap_plugin.computing_core.sbom.parser as parser

        monkeypatch.setattr(parser, "_load", lambda data: pytest.fail("the body was read"))
        with pytest.raises(ValueError, match="is not parsed; use record_document"):
            parse_cyclonedx(b"{}", host_id=HOST, verification=verification)


class TestVulnerabilitiesStaySignatureOnly:
    def test_the_vulnerability_reader_refuses_it(self, corpus_bytes, monkeypatch):
        import tap_plugin.computing_core.sbom.vulnerabilities as vulnerabilities

        monkeypatch.setattr(vulnerabilities, "_load", lambda data: pytest.fail("the body was read"), raising=False)
        with pytest.raises(ValueError, match="is not parsed"):
            parse_cyclonedx_vulnerabilities(corpus_bytes, verification=FROM_SOURCE)


class TestRecordedWithoutParsing:
    def test_a_document_the_caller_does_not_parse_is_recorded_with_its_source(self):
        body = b"SPDXVersion: SPDX-2.3 not json at all"
        batch = record_document(body, verification=FROM_SOURCE, subject_digest=SUBJECT)
        document = row(batch)
        assert (document["verified"], document["authenticated_source"], document["format"]) == (None, SOURCE, "unknown")
        assert document["content_digest"] == hashlib.sha256(body).hexdigest()
        assert len(batch.nodes) == 1 and not batch.edges


def _create(payload: dict):
    result = create_node(TYPE, payload)
    assert result.success, f"create_node failed: {result.errors}"
    return get_model_class(TYPE).objects.get(entity=Entity.objects.get(pk=result.entity_id))


@pytest.mark.django_db
class TestTheRowIsStrict:
    DOCUMENT = {"content_digest": "ab" * 32, "format": "cyclonedx", "spec_version": "1.6", "serial_number": SERIAL, "revision": 1, "subject_digest": SUBJECT}

    def test_a_source_authenticated_row_is_accepted(self):
        node = _create({**self.DOCUMENT, "verified": None, "authenticated_source": SOURCE})
        assert node.authenticated_source == SOURCE and node.verified is None

    @pytest.mark.parametrize(
        "fields",
        [
            {"verified": True, "signer": "ci"},
            {"verified": False, "verification_note": "subject-digest"},
            {"verified": None, "verification_note": "no attestation was published"},
        ],
    )
    def test_a_source_beside_any_other_outcome_is_refused(self, fields):
        result = create_node(TYPE, {**self.DOCUMENT, **fields, "authenticated_source": SOURCE})
        assert not result.success and "authenticated_source" in str(result.errors)

    @pytest.mark.parametrize("blank", [" ", "   ", "\u00a0"])
    def test_a_source_that_is_only_whitespace_is_refused(self, blank):
        result = create_node(TYPE, {**self.DOCUMENT, "verified": None, "authenticated_source": blank})
        assert not result.success and "authenticated_source" in str(result.errors)

    @pytest.mark.parametrize("bad", ["a\nb", "a\x00b", "tab\there", "x" * 513, "trailing\n"])
    def test_a_source_with_a_control_character_or_over_its_column_is_refused(self, bad):
        """The model checks it as it checks a signer, whether or not the caller went through Verification."""
        assert not create_node(TYPE, {**self.DOCUMENT, "verified": None, "authenticated_source": bad}).success
        instance = get_model_class(TYPE)(**{**self.DOCUMENT, "verified": None, "authenticated_source": bad})
        schema = get_model_class(TYPE).FIELD_VALIDATION_SCHEMA["authenticated_source"]["schema"]
        import jsonschema

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance.authenticated_source, schema)

    def test_it_is_never_current(self):
        _create({**self.DOCUMENT, "revision": 5, "verified": None, "authenticated_source": SOURCE})
        assert get_model_class(TYPE).current(SUBJECT, SERIAL) is None
        signed = _create({**self.DOCUMENT, "content_digest": "cd" * 32, "revision": 1, "verified": True, "signer": "ci"})
        assert get_model_class(TYPE).current(SUBJECT, SERIAL).pk == signed.pk
