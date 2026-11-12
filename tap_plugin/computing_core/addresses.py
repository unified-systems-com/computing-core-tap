"""Address classification shared by the address-bearing types (req-computing-core-ip-4).

An ``ip_address`` node is one address on one network, shared by every observer that sees it.
Three kinds of address cannot be that, because their meaning depends on the machine or link
they are seen from:

- **loopback** (``127.0.0.0/8``, ``::1``): every machine has its own. It belongs on
  ``loopback_address``, keyed to its host.
- **wildcard** (``0.0.0.0``, ``::``): a listener bound to "every address on this host", not one
  address.
- **link-local** (``169.254.0.0/16``, ``fe80::/10``): valid only on one network segment, and
  reused on every segment.

An IPv4-mapped IPv6 address (``::ffff:127.0.0.1``) is classified by the IPv4 address it carries.
"""

import ipaddress

LOOPBACK = "loopback"
WILDCARD = "wildcard"
LINK_LOCAL = "link-local"


def parse_address(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Parse one IP address, unwrapping an IPv4-mapped IPv6 address. Raises ValueError."""
    addr = ipaddress.ip_address(value)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        return addr.ipv4_mapped
    return addr


def host_scoped_kind(value: str) -> str | None:
    """The kind of host- or link-scoped address ``value`` is, or None for a shareable address.

    Raises ValueError when ``value`` is not an IP address.
    """
    addr = parse_address(value)
    if addr.is_loopback:
        return LOOPBACK
    if addr.is_unspecified:
        return WILDCARD
    if addr.is_link_local:
        return LINK_LOCAL
    return None
