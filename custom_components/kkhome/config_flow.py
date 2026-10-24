"""Config flow for KK Home integration."""

from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import KKHomeApiClient, KKHomeApiError, KKHomeAuthError
from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KKHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KK Home."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step using email and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            entry_data = {
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
            }

            client = KKHomeApiClient(self.hass, entry_data)
            try:
                token = await client.async_authenticate()
                await client.async_get_devices()
                entry_data["token"] = token
            except KKHomeAuthError as err:
                _LOGGER.error("KK Home authentication failed: %s", err)
                errors["base"] = "invalid_auth"
            except KKHomeApiError as err:
                _LOGGER.error("KK Home connection failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected error during KK Home login: %s", err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(username.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"KK Home ({username})",
                    data=entry_data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
