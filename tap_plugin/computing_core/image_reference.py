"""The canonical form of an image tag's registry and repository (req-computing-core-image-tag-6).

Docker lets a reference leave out parts that Docker Hub supplies: ``nginx:1.25`` is
``docker.io/library/nginx:1.25``, and ``myorg/app:2`` is ``docker.io/myorg/app:2``. Writers do not all
spell a tag the same way. ECS reports what the task definition wrote, and Anchore reports the expanded
form. If each kept its own spelling, one tag would be two nodes, and an image would never meet the tag
a scanner wrote for it. So computing_core keys a tag by the reference Docker would pull, and each writer
sends the parts as written.

The rules are Docker's own, from ``splitDockerDomain`` in distribution/reference v0.6.0
(``normalize.go``, https://github.com/distribution/reference/blob/v0.6.0/normalize.go). That is the
grammar ``docker pull`` and containerd use:

- The first ``/``-separated component is a registry host only when it contains ``.`` or ``:``, is
  ``localhost``, or has an upper-case letter (a repository path is lower-case, so an upper-case
  component can only be a host). Otherwise the whole name is a Docker Hub repository.
- A name with no registry host is on ``docker.io``.
- ``index.docker.io`` (Docker Hub's legacy name in that file) is ``docker.io``. So is
  ``registry-1.docker.io``, the host Docker Hub's registry API is served from
  (``DefaultRegistryHost`` in moby/moby ``daemon/pkg/registry/config.go``). Docker's reference grammar
  does not fold that host, but it names the same registry, so a writer that reports the API host
  joins too.
- A one-component repository on ``docker.io`` is an official image, under ``library/``. This applies
  only on Docker Hub. ``localhost:5000/app`` stays ``app``.

Only the registry and the repository change. A tag is kept as written. A missing tag is not given
``latest``: a reference with no tag makes no ``image_tag`` (req-computing-core-image-tag). A digest is
not part of a tag's key, so nothing here touches one. Case is kept as written, as Docker keeps it.

This module imports nothing. Writers never import it: they send ``(registry, repository, tag)`` by type
slug, and the model applies these rules through core's natural-key hook
(``ImageTag.normalize_natural_key``), which core runs wherever it resolves or writes a key. That is
how every writer gets the same rules.
"""

from __future__ import annotations

from typing import Final

__all__ = ["DOCKER_HUB", "canonical_repository"]

#: Docker Hub's canonical registry name (``defaultDomain``).
DOCKER_HUB: Final[str] = "docker.io"
#: Other names for Docker Hub: ``legacyDefaultDomain``, and moby's ``DefaultRegistryHost``.
DOCKER_HUB_ALIASES: Final[frozenset[str]] = frozenset({"index.docker.io", "registry-1.docker.io"})
#: The namespace of Docker Hub's official images (``officialRepoPrefix``).
OFFICIAL_NAMESPACE: Final[str] = "library/"
#: A reserved name that is always a registry host.
LOCALHOST: Final[str] = "localhost"


def _is_host(component: str) -> bool:
    return component == LOCALHOST or any(c in component for c in ".:") or component.lower() != component


def canonical_repository(registry: str, repository: str) -> tuple[str, str]:
    """The canonical ``(registry, repository)`` of an image name, by Docker's rules.

    ``registry`` is the reference's host as the writer split it. ``""`` means the reference named no
    host. The two parts are joined and split again by Docker's rule, so a writer that put the whole
    name in ``repository`` gets the same answer as one that split it. A part that is already canonical
    comes back unchanged. An empty ``repository`` comes back unchanged with its registry.

    >>> canonical_repository("", "nginx")
    ('docker.io', 'library/nginx')
    >>> canonical_repository("", "myorg/app")
    ('docker.io', 'myorg/app')
    >>> canonical_repository("index.docker.io", "nginx")
    ('docker.io', 'library/nginx')
    >>> canonical_repository("localhost:5000", "app")
    ('localhost:5000', 'app')
    """
    if not repository:
        # No repository is no name: left as it is, for the model's validation to refuse.
        return registry, repository
    name = f"{registry}/{repository}" if registry else repository
    first, sep, rest = name.partition("/")
    if sep and _is_host(first):
        host, path = first, rest
    else:
        host, path = DOCKER_HUB, name
    if host in DOCKER_HUB_ALIASES:
        host = DOCKER_HUB
    if host == DOCKER_HUB and "/" not in path:
        path = OFFICIAL_NAMESPACE + path
    return host, path
