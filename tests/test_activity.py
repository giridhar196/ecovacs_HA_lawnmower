"""Unit tests for work-state activity mapping."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components/ecovacs_open"


def _load(name: str, path: Path, package_globals: dict | None = None):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    if package_globals:
        module.__dict__.update(package_globals)
    sys_modules_name = name
    import sys

    sys.modules[sys_modules_name] = module
    spec.loader.exec_module(module)
    return module


import sys
import types

pkg = types.ModuleType("custom_components.ecovacs_open")
pkg.__path__ = [str(ROOT)]
sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
sys.modules["custom_components.ecovacs_open"] = pkg
const = _load("custom_components.ecovacs_open.const", ROOT / "const.py")
models = _load("custom_components.ecovacs_open.models", ROOT / "models.py")
MowerDeviceData = models.MowerDeviceData


def _data(clean_st: str | None, charge_st: str | None) -> MowerDeviceData:
    state: dict = {}
    if clean_st is not None:
        state["cleanSt"] = clean_st
    if charge_st is not None:
        state["chargeSt"] = charge_st
    return MowerDeviceData(nickname="Goat", raw_device={}, work_state=state)


def test_mowing() -> None:
    assert _data("s", "i").activity == "mowing"


def test_paused() -> None:
    assert _data("p", "i").activity == "paused"


def test_returning() -> None:
    assert _data("h", "g").activity == "returning"


def test_docked_charging() -> None:
    assert _data("h", "charging").activity == "docked"


def test_docked_idle() -> None:
    assert _data("h", "i").activity == "docked"
