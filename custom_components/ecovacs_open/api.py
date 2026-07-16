"""Ecovacs Open Platform API client."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import (
    ACT_CHARGE_START,
    ACT_PAUSE,
    ACT_RESUME,
    ACT_START,
    ACT_STOP,
    CMD_CHARGE,
    CMD_CLEAN,
    CMD_GET_WORK_STATE,
    ENDPOINT_CTL,
    ENDPOINT_DEVICE_LIST,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = ClientTimeout(total=15)


class EcovacsOpenApiError(Exception):
    """Raised when the Ecovacs Open API returns an error."""

    def __init__(self, message: str, code: int | None = None) -> None:
        """Initialize."""
        super().__init__(message)
        self.code = code


class EcovacsOpenApi:
    """Async client for https://open.ecovacs.com robot APIs."""

    def __init__(
        self,
        session: ClientSession,
        api_key: str,
        api_url: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._api_key = api_key
        self._api_url = api_url.rstrip("/")

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return robots bound to the API key account.

        Open Platform may return either nickname strings
        (``["Lawn mower"]``) or device objects.
        """
        data = await self._request(ENDPOINT_DEVICE_LIST, method="get")
        devices = _as_device_list(data)
        if devices:
            return devices

        # Richer fallback used by some Open Platform deployments.
        try:
            skill_data = await self._request("robot/skill/deviceList", method="get")
        except EcovacsOpenApiError:
            return []
        return _as_device_list(skill_data)

    async def async_get_work_state(self, nickname: str) -> dict[str, Any]:
        """Return work-state payload for a robot nickname."""
        data = await self._request(
            ENDPOINT_CTL,
            {
                "nickName": nickname,
                "cmd": CMD_GET_WORK_STATE,
                "act": "",
            },
        )
        return _extract_work_state(data)

    async def async_start_mowing(self, nickname: str) -> None:
        """Start mowing (Clean act=s)."""
        await self._request(
            ENDPOINT_CTL,
            {"nickName": nickname, "cmd": CMD_CLEAN, "act": ACT_START},
        )

    async def async_resume_mowing(self, nickname: str) -> None:
        """Resume mowing (Clean act=r)."""
        await self._request(
            ENDPOINT_CTL,
            {"nickName": nickname, "cmd": CMD_CLEAN, "act": ACT_RESUME},
        )

    async def async_pause(self, nickname: str) -> None:
        """Pause mowing (Clean act=p)."""
        await self._request(
            ENDPOINT_CTL,
            {"nickName": nickname, "cmd": CMD_CLEAN, "act": ACT_PAUSE},
        )

    async def async_stop(self, nickname: str) -> None:
        """Stop mowing (Clean act=h)."""
        await self._request(
            ENDPOINT_CTL,
            {"nickName": nickname, "cmd": CMD_CLEAN, "act": ACT_STOP},
        )

    async def async_dock(self, nickname: str) -> None:
        """Send the robot back to the charging station."""
        await self._request(
            ENDPOINT_CTL,
            {
                "nickName": nickname,
                "cmd": CMD_CHARGE,
                "act": ACT_CHARGE_START,
            },
        )

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        method: str = "post",
    ) -> Any:
        """Call an Open Platform endpoint and return the data field."""
        url = f"{self._api_url}/{endpoint}"
        payload = {k: str(v) for k, v in (params or {}).items()}
        payload["ak"] = self._api_key

        try:
            if method.lower() == "get":
                async with self._session.get(
                    url,
                    params=payload,
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    body = await response.json(content_type=None)
                    if response.status >= 400:
                        raise EcovacsOpenApiError(
                            f"HTTP {response.status}: {body}",
                            code=response.status,
                        )
            else:
                async with self._session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    body = await response.json(content_type=None)
                    if response.status >= 400:
                        raise EcovacsOpenApiError(
                            f"HTTP {response.status}: {body}",
                            code=response.status,
                        )
        except ClientError as err:
            raise EcovacsOpenApiError(f"Request failed: {err}") from err

        return self._parse_response(body)

    @staticmethod
    def _parse_response(body: Any) -> Any:
        """Validate Open Platform response envelope and return data."""
        if not isinstance(body, dict):
            raise EcovacsOpenApiError(f"Unexpected response: {body!r}")

        code = body.get("code", body.get("status"))
        msg = body.get("msg") or body.get("message") or "unknown error"

        if code not in (0, "0", None):
            # Some successful responses omit code; treat non-zero as failure.
            if code is not None:
                raise EcovacsOpenApiError(str(msg), code=int(code) if str(code).lstrip("-").isdigit() else None)

        return body.get("data", body)


def device_nickname(device: str | dict[str, Any]) -> str:
    """Extract a usable nickname from a device-list entry."""
    if isinstance(device, str) and device.strip():
        return device.strip()
    if isinstance(device, dict):
        for key in ("nickname", "nickName", "nick", "name", "deviceName"):
            value = device.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    raise EcovacsOpenApiError(f"Device has no nickname: {device!r}")


def _as_device_list(data: Any) -> list[dict[str, Any]]:
    """Normalize device-list payloads into a list of dicts."""
    raw: list[Any]
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        for key in ("list", "devices", "robots", "data"):
            if isinstance(data.get(key), list):
                raw = data[key]
                break
        else:
            return []
    else:
        return []

    devices: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            devices.append({"nickname": item.strip()})
        elif isinstance(item, dict):
            devices.append(item)
    return devices


def _extract_work_state(data: Any) -> dict[str, Any]:
    """Normalize GetWorkState data into a flat status dict."""
    if not isinstance(data, dict):
        return {}

    ctl = data.get("ctl")
    if isinstance(ctl, dict):
        inner = ctl.get("data")
        if isinstance(inner, dict):
            return inner

    if "cleanSt" in data or "chargeSt" in data:
        return data

    nested = data.get("data")
    if isinstance(nested, dict):
        return _extract_work_state(nested)

    return data
