"""Config flow — Cloud account (full) or Open Platform AK (limited)."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import voluptuous as vol
from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator, create_rest_config
from deebot_client.exceptions import DeebotError, InvalidAuthenticationError
from deebot_client.util import md5
from homeassistant import config_entries
from homeassistant.const import CONF_COUNTRY, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EcovacsOpenApi, EcovacsOpenApiError, device_nickname
from .const import (
    API_URL_CHINA,
    API_URL_WORLDWIDE,
    CONF_API_KEY,
    CONF_API_URL,
    CONF_MODE,
    DOMAIN,
    MODE_CLOUD,
    MODE_OPEN,
)
from .util import get_client_device_id

_LOGGER = logging.getLogger(__name__)


class EcovacsOpenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize."""
        self._mode: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Choose integration mode."""
        if user_input is not None:
            self._mode = user_input[CONF_MODE]
            if self._mode == MODE_CLOUD:
                return await self.async_step_cloud()
            return await self.async_step_open()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODE, default=MODE_CLOUD): vol.In(
                        [MODE_CLOUD, MODE_OPEN]
                    )
                }
            ),
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Cloud account login."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            country = user_input[CONF_COUNTRY].upper()
            name = user_input.get(CONF_NAME) or "Ecovacs Lawn Mower"

            await self.async_set_unique_id(f"cloud:{username.lower()}")
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            device_id = get_client_device_id(self.hass)
            authenticator = Authenticator(
                create_rest_config(
                    session, device_id=device_id, alpha_2_country=country
                ),
                username,
                md5(password),
            )
            api = ApiClient(authenticator)
            try:
                devices = await api.get_devices()
            except InvalidAuthenticationError:
                errors["base"] = "invalid_auth"
            except DeebotError:
                _LOGGER.debug("Cloud connect failed", exc_info=True)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected cloud login error")
                errors["base"] = "unknown"
            else:
                if not devices.mqtt and not devices.xmpp:
                    errors["base"] = "no_devices"
                else:
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_MODE: MODE_CLOUD,
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                            CONF_COUNTRY: country,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_COUNTRY, default="US"): selector.CountrySelector(),
                vol.Optional(CONF_NAME, default="Ecovacs Lawn Mower"): str,
            }
        )
        return self.async_show_form(
            step_id="cloud", data_schema=schema, errors=errors
        )

    async def async_step_open(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Open Platform AK (limited)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            api_url = user_input[CONF_API_URL]
            name = user_input.get(CONF_NAME) or "Ecovacs Open"

            unique = hashlib.sha256(f"{api_url}:{api_key}".encode()).hexdigest()[:16]
            await self.async_set_unique_id(unique)
            self._abort_if_unique_id_configured()

            api = EcovacsOpenApi(async_get_clientsession(self.hass), api_key, api_url)
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
                            CONF_MODE: MODE_OPEN,
                            CONF_API_KEY: api_key,
                            CONF_API_URL: api_url,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_API_URL, default=API_URL_WORLDWIDE): vol.In(
                    [API_URL_WORLDWIDE, API_URL_CHINA]
                ),
                vol.Optional(CONF_NAME, default="Ecovacs Open"): str,
            }
        )
        return self.async_show_form(step_id="open", data_schema=schema, errors=errors)
