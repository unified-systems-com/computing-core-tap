"""Event time (core's req-grid-entity-event-time, tap 0.4.7): what each computing_core model declares, and
what core derives from it.

The first class pins the declarations, so a model added later without one, or one that names the wrong
field, fails here. The second applies core's own derivation to plain values: an image host is open-ended
from its build, and a host that is not an image (no build time) has no event time at all.
"""

from datetime import UTC, datetime

from tap_plugin.computing_core.models import (
    ApplicationFlow,
    CryptoProvider,
    File,
    Host,
    ImageTag,
    IpAddress,
    KubernetesCluster,
    KubernetesContainer,
    KubernetesNamespace,
    KubernetesNode,
    KubernetesPod,
    Library,
    LoopbackAddress,
    Module,
    Network,
    NetworkInterface,
    OperatingSystem,
    OsGroup,
    OsUser,
    Package,
    Port,
    PrivateKey,
    Program,
    PublicKey,
    SbomDocument,
    SourcePackage,
    TcpConnection,
    WebDocument,
    WebHost,
)

from tap_grid.event_time import NO_EVENT_TIME, Interval, Moment, declaration_problems, derive
from tap_grid.registry import get_model_class, list_entity_types

DECLARED = {
    Host: Interval(start="image_built_at", kind="created"),
    SbomDocument: Moment(field="produced_at", kind="created"),
    ApplicationFlow: NO_EVENT_TIME,
    CryptoProvider: NO_EVENT_TIME,
    File: NO_EVENT_TIME,
    ImageTag: NO_EVENT_TIME,
    IpAddress: NO_EVENT_TIME,
    KubernetesCluster: NO_EVENT_TIME,
    KubernetesContainer: NO_EVENT_TIME,
    KubernetesNamespace: NO_EVENT_TIME,
    KubernetesNode: NO_EVENT_TIME,
    KubernetesPod: NO_EVENT_TIME,
    Library: NO_EVENT_TIME,
    LoopbackAddress: NO_EVENT_TIME,
    Module: NO_EVENT_TIME,
    Network: NO_EVENT_TIME,
    NetworkInterface: NO_EVENT_TIME,
    OperatingSystem: NO_EVENT_TIME,
    OsGroup: NO_EVENT_TIME,
    OsUser: NO_EVENT_TIME,
    Package: NO_EVENT_TIME,
    Port: NO_EVENT_TIME,
    PrivateKey: NO_EVENT_TIME,
    Program: NO_EVENT_TIME,
    PublicKey: NO_EVENT_TIME,
    SourcePackage: NO_EVENT_TIME,
    TcpConnection: NO_EVENT_TIME,
    WebDocument: NO_EVENT_TIME,
    WebHost: NO_EVENT_TIME,
}

BUILT = datetime(2026, 11, 1, 8, tzinfo=UTC)


class TestDeclarations:
    def test_every_model_of_the_plugin_decides(self) -> None:
        own = {get_model_class(slug) for slug in list_entity_types() if slug.startswith("computing_core__")}
        assert own == set(DECLARED)
        assert {model: model.EVENT_TIME for model in own} == DECLARED

    def test_core_accepts_each_declaration(self) -> None:
        for model in DECLARED:
            assert declaration_problems(model) == [], model.__name__


class TestDerivation:
    def test_an_image_host_holds_from_its_build_with_no_end(self) -> None:
        derived = derive(Host.EVENT_TIME, {"image_built_at": BUILT}.get)
        assert (derived.event_start, derived.event_end, derived.kind) == (BUILT, None, "created")

    def test_a_host_that_is_not_an_image_has_none(self) -> None:
        derived = derive(Host.EVENT_TIME, {"image_built_at": None}.get)
        assert (derived.event_start, derived.event_end, derived.kind) == (None, None, None)

    def test_an_sbom_document_is_a_moment_at_its_timestamp(self) -> None:
        derived = derive(SbomDocument.EVENT_TIME, {"produced_at": BUILT}.get)
        assert (derived.event_start, derived.event_end, derived.kind) == (BUILT, BUILT, "created")
