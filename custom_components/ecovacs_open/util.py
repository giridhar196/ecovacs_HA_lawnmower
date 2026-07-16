"""Helpers."""

from __future__ import annotations

import random
import string

from homeassistant.core import HomeAssistant
from homeassistant.util import slugify


def get_client_device_id(hass: HomeAssistant) -> str:
    """Return a client device id for Ecovacs auth."""
    location = slugify(hass.config.location_name or "home")
    suffix = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(4)
    )
    return f"HA-{location}-{suffix}"[:32]
