"""No Computing Core type keeps a free-form record (req-computing-core-models-7).

The eight types that carried a `configuration` JSON field had no collector to fill it; a verbatim
record with no reader is only a place for secret material (a private key's) or personal data to
collect. The field is gone, and a write that carries it is refused.
"""

import tomllib
from pathlib import Path

import pytest
import tap_plugin.computing_core.models as computing  # noqa: F401 — trigger model registration

from tap_grid.registry import get_model_class
from tap_grid.services import create_node

MANIFEST = tomllib.loads((Path(__file__).resolve().parents[1] / "tap-plugin.toml").read_text())

#: A minimal payload each formerly-configured type accepts.
MINIMAL: dict[str, dict] = {
    "computing_core__network_interface": {"interface_name": "eth0"},
    "computing_core__ip_address": {"network_name": "corp", "address": "10.0.0.1"},
    "computing_core__port": {"network_name": "corp", "address": "10.0.0.1", "transport": "tcp", "port_number": 443},
    "computing_core__tcp_connection": {"name": "c1"},
    "computing_core__program": {"program_name": "sshd"},
    "computing_core__file": {"file_path": "/etc/ssh/sshd_config"},
    "computing_core__public_key": {"fingerprint": "SHA256:abc"},
    "computing_core__private_key": {"fingerprint": "SHA256:abc"},
}


@pytest.mark.parametrize("type_slug", sorted(MANIFEST["models"]))
def test_no_type_declares_configuration(type_slug: str) -> None:
    model = get_model_class(type_slug)
    assert "configuration" not in model.FIELD_CRUD_SCHEMA
    assert "configuration" not in model.FIELD_VALIDATION_SCHEMA
    assert "configuration" not in {f.name for f in model._meta.get_fields()}


@pytest.mark.django_db
@pytest.mark.parametrize("type_slug", sorted(MINIMAL))
def test_configuration_write_is_refused(type_slug: str) -> None:
    payload = MINIMAL[type_slug]
    assert create_node(type_slug, payload).success, type_slug
    assert not create_node(type_slug, {**payload, "configuration": {"key_material": "sentinel"}}).success, type_slug
