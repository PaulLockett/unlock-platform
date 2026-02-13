"""Connector factory — maps source_type strings to connector classes.

Adding a new data source connector:
  1. Create a new subclass of BaseConnector in this package
  2. Add one entry to _CONNECTOR_CLASSES below
  3. That's it — the activities and factory handle the rest
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from unlock_source_access.connectors.posthog import PostHogConnector
from unlock_source_access.connectors.rb2b import RB2BConnector
from unlock_source_access.connectors.unipile import UnipileConnector
from unlock_source_access.connectors.x import XConnector

if TYPE_CHECKING:
    from unlock_shared.source_models import SourceConfig

    from unlock_source_access.connectors.base import BaseConnector

_CONNECTOR_CLASSES: dict[str, type[BaseConnector]] = {
    "unipile": UnipileConnector,
    "x": XConnector,
    "posthog": PostHogConnector,
    "rb2b": RB2BConnector,
}


def get_connector(config: SourceConfig) -> BaseConnector:
    """Instantiate the correct connector for the given source type."""
    cls = _CONNECTOR_CLASSES.get(config.source_type)
    if cls is None:
        supported = ", ".join(sorted(_CONNECTOR_CLASSES.keys()))
        raise ValueError(
            f"Unknown source_type '{config.source_type}'. Supported: {supported}"
        )
    return cls(config)
