"""Data update coordinator for KK Home."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KKHomeApiClient, KKHomeApiError, KKHomeAuthError
from .const import DEFAULT_POLL_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KKHomeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Data update coordinator for KK Home devices."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.api = KKHomeApiClient(hass, dict(entry.data))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from KK Home API."""
        try:
            return await self.api.async_get_devices()
        except KKHomeAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except KKHomeApiError as err:
            raise UpdateFailed(str(err)) from err
