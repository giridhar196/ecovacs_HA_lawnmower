"""Tests for API response helpers."""

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/ecovacs_open"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pkg = types.ModuleType("custom_components.ecovacs_open")
pkg.__path__ = [str(ROOT)]
sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
sys.modules["custom_components.ecovacs_open"] = pkg
_load("custom_components.ecovacs_open.const", ROOT / "const.py")
api = _load("custom_components.ecovacs_open.api", ROOT / "api.py")

EcovacsOpenApi = api.EcovacsOpenApi
EcovacsOpenApiError = api.EcovacsOpenApiError
_extract_work_state = api._extract_work_state
device_nickname = api.device_nickname
_as_device_list = api._as_device_list


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
    assert device_nickname("Lawn mower") == "Lawn mower"


def test_as_device_list_strings() -> None:
    assert _as_device_list(["Lawn mower"]) == [{"nickname": "Lawn mower"}]
