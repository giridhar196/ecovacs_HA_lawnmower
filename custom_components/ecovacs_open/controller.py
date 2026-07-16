"""Ecovacs cloud controller (deebot-client / MQTT)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from functools import partial
from typing import Any

from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator, create_rest_config
from deebot_client.capabilities import DeviceType
from deebot_client.device import Device
from deebot_client.exceptions import DeebotError, InvalidAuthenticationError
from deebot_client.mqtt_client import MqttClient, create_mqtt_config
from deebot_client.util import md5

from homeassistant.const import CONF_COUNTRY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from .util import get_client_device_id

_LOGGER = logging.getLogger(__name__)


class EcovacsCloudController:
    """Authenticate and manage Ecovacs MQTT devices."""

    def __init__(self, hass: HomeAssistant, config: Mapping[str, Any]) -> None:
        """Initialize."""
        self._hass = hass
        self._devices: list[Device] = []
        self._device_id = get_client_device_id(hass)
        country = config[CONF_COUNTRY]

        self._authenticator = Authenticator(
            create_rest_config(
                aiohttp_client.async_get_clientsession(hass),
                device_id=self._device_id,
                alpha_2_country=country,
            ),
            config[CONF_USERNAME],
            md5(config[CONF_PASSWORD]),
        )
        self._api_client = ApiClient(self._authenticator)
        self._mqtt_config_fn = partial(
            create_mqtt_config,
            device_id=self._device_id,
            country=country,
        )
        self._mqtt_client: MqttClient | None = None
        # nickname/did -> known zone ids from last refresh
        self.zone_ids: dict[str, list[str]] = {}

    async def initialize(self) -> None:
        """Connect and initialize mower devices."""
        try:
            devices = await self._api_client.get_devices()
            if not devices.mqtt:
                raise ConfigEntryNotReady("No MQTT Ecovacs devices found")

            mqtt = await self._get_mqtt_client()
            mqtt_devices = [Device(info, self._authenticator) for info in devices.mqtt]

            async with asyncio.TaskGroup() as tg:

                async def _init(device: Device) -> None:
                    await device.initialize(mqtt)
                    # Prefer mowers; still keep unknown GOAT-like devices.
                    if (
                        device.capabilities.device_type is DeviceType.MOWER
                        or "GOAT" in str(device.device_info.get("deviceName", "")).upper()
                        or str(device.device_info.get("product_category", "")).upper()
                        == "GOATBOT"
                    ):
                        self._devices.append(device)
                    else:
                        _LOGGER.debug(
                            "Skipping non-mower device %s",
                            device.device_info.get("deviceName"),
                        )
                        await device.teardown()

                for device in mqtt_devices:
                    tg.create_task(_init(device))

            for device_config in devices.not_supported:
                _LOGGER.warning(
                    "Device not supported by deebot-client yet: %s",
                    device_config.get("deviceName") or device_config,
                )

        except InvalidAuthenticationError as err:
            raise ConfigEntryError("Invalid Ecovacs credentials") from err
        except DeebotError as err:
            raise ConfigEntryNotReady("Ecovacs cloud setup failed") from err
        except ExceptionGroup as err:
            # TaskGroup wraps device init failures
            raise ConfigEntryNotReady("Ecovacs cloud setup failed") from err

        if not self._devices:
            raise ConfigEntryNotReady("No lawn mower devices found on this account")

        _LOGGER.debug("Initialized %s mower device(s)", len(self._devices))

    async def teardown(self) -> None:
        """Disconnect."""
        for device in self._devices:
            await device.teardown()
        if self._mqtt_client is not None:
            await self._mqtt_client.disconnect()
        await self._authenticator.teardown()

    async def _get_mqtt_client(self) -> MqttClient:
        """Create and verify MQTT client."""
        if self._mqtt_client is None:
            config = await self._hass.async_add_executor_job(self._mqtt_config_fn)
            mqtt = MqttClient(config, self._authenticator)
            await mqtt.verify_config()
            self._mqtt_client = mqtt
        return self._mqtt_client

    @property
    def devices(self) -> list[Device]:
        """Return mower devices."""
        return self._devices

    def get_device(self, did: str) -> Device | None:
        """Return device by did."""
        for device in self._devices:
            if device.device_info.get("did") == did:
                return device
        return None
