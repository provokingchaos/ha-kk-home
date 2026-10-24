"""Config flow for KK Home integration."""
import logging
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect."""
    headers = {
        "Host": "api.kksecurityhome.com",
        "k-tenant": "kawden",
        "k-version": "3.5.0",
        "token": data["token"],
        "User-Agent": "KKHome/3.5.0 (iPhone; iOS 27.0.1; Scale/3.00)",
        "phoneName": "iPhone19,3",
        "k-language": "en_US",
        "k-signv": "1.0.0",
        "Content-Length": "0",
    }
    
    url = "https://api.kksecurityhome.com/v3/user/device/list"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, timeout=10) as response:
            if response.status != 200:
                raise InvalidAuth
            res = await response.json()
            if res.get("code") != 200:
                raise InvalidAuth

    return {"title": "KK Home"}

class KKHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KK Home."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("token"): str}),
            errors=errors,
        )

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
