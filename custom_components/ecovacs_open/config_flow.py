"""Config flow for Ecovacs Open lawn mower integration."""

from __future__ import annotations

import hashlib
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EcovacsOpenApi, EcovacsOpenApiError, device_nickname
from .const import (
    API_URL_CHINA,
    API_URL_WORLDWIDE,
    CONF_API_KEY,
    CONF_API_URL,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_API_URL, default=API_URL_WORLDWIDE): vol.In(
            [API_URL_WORLDWIDE, API_URL_CHINA]
        ),
        vol.Optional(CONF_NAME, default="Ecovacs Open"): str,
    }
)


class EcovacsOpenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecovacs Open."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            api_url = user_input[CONF_API_URL]
            name = user_input.get(CONF_NAME) or "Ecovacs Open"

            unique = hashlib.sha256(f"{api_url}:{api_key}".encode()).hexdigest()[:16]
            await self.async_set_unique_id(unique)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = EcovacsOpenApi(session, api_key, api_url)

            try:
                devices = await api.async_get_devices()
                nicknames = [device_nickname(d) for d in devices]
            except EcovacsOpenApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                if not nicknames:
                    errors["base"] = "no_devices"
                else:
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_API_KEY: api_key,
                            CONF_API_URL: api_url,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
