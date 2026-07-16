"""Tests for API response helpers."""

import pytest

from custom_components.ecovacs_open.api import (
    EcovacsOpenApi,
    EcovacsOpenApiError,
    _extract_work_state,
    device_nickname,
)


def test_parse_success_code_zero() -> None:
    assert EcovacsOpenApi._parse_response({"code": 0, "msg": "OK", "data": [1]}) == [1]


def test_parse_success_status_zero() -> None:
    assert EcovacsOpenApi._parse_response(
        {"status": 0, "message": "success", "data": [{"nickname": "Goat"}]}
    ) == [{"nickname": "Goat"}]


def test_parse_error() -> None:
    with pytest.raises(EcovacsOpenApiError):
        EcovacsOpenApi._parse_response({"code": 401, "msg": "unauthorized"})


def test_extract_work_state_nested() -> None:
    payload = {
        "ctl": {
            "data": {
                "ret": "ok",
                "cleanSt": "h",
                "chargeSt": "charging",
                "stationSt": "i",
            }
        }
    }
    state = _extract_work_state(payload)
    assert state["cleanSt"] == "h"
    assert state["chargeSt"] == "charging"


def test_device_nickname() -> None:
    assert device_nickname({"nickname": "Front Lawn"}) == "Front Lawn"
    assert device_nickname({"nickName": "Back"}) == "Back"
