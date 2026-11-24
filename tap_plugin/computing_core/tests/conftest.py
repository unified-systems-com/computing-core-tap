"""Shared test scaffolding for the computing_core plugin's suite."""


def dimension_view(entity) -> dict:
    """An entity's dimensions as ``{name: value}``, whichever way the grid under test stores them.

    A grid from tap 0.3.4 or earlier stores that map directly. A later one keys it by Dimension
    node and wraps each value; its own ``view`` turns that back into names and values.
    """
    try:
        from tap_grid.dimension_names import view
    except ImportError:
        return dict(entity.dimensions or {})
    return view(entity.dimensions)


def keyed(type_slug: str, payload: dict) -> tuple[dict, dict]:
    """Split a test payload into the typed payload and the identity dimensions its key names.

    A type keyed on a dimension (form 3, unified-systems-com/tap#1355) reads that value from the
    envelope's dimensions, never the payload. Tests spell it in the payload by the dimension's last
    name segment (``host_type``, ``kubernetes_cluster_type``, ``host``, ``network_name``) and this
    moves it out, so a fixture still reads as one record.
    """
    from tap_grid.natural_key import dimension_name, keyed_dimension_entries
    from tap_grid.registry import get_model_class

    fields, dimensions = dict(payload), {}
    for entry in keyed_dimension_entries(get_model_class(type_slug)):
        name = dimension_name(entry)
        alias = name.rsplit(".", 1)[-1]
        if alias in fields:
            dimensions[name] = fields.pop(alias)
    return fields, dimensions


def create_node(type_slug: str, payload: dict, **kwargs):
    """``tap_grid.services.create_node`` for a payload that may spell its identity dimensions (see :func:`keyed`)."""
    from tap_grid.service_types import WriteOperation
    from tap_grid.services import write_batch

    fields, dimensions = keyed(type_slug, payload)
    result = write_batch(
        [WriteOperation(verb="create_node", type_slug=type_slug, payload=fields, dimensions=dimensions or None)],
        **kwargs,
    )
    return result.results[0] if result.results else result


def host_key(host_type: str, stable_id: str) -> str:
    """A host's spine natural key, the value of ``tap.computing.host`` for what it owns."""
    from tap_grid.natural_key import encode_key_part

    return f"{encode_key_part(host_type)}|{encode_key_part(stable_id)}"
