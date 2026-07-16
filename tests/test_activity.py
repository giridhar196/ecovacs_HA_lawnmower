"""Unit tests for work-state activity mapping."""

from custom_components.ecovacs_open.models import MowerDeviceData


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
