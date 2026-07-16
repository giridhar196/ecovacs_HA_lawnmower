"""Pure data models for Ecovacs Open (no Home Assistant imports)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import (
    CHARGE_ST_DOCKED,
    CHARGE_ST_RETURN_PAUSED,
    CHARGE_ST_RETURNING,
    CLEAN_ST_MOWING,
    CLEAN_ST_PAUSED,
)


@dataclass(slots=True)
class MowerDeviceData:
    """Snapshot for one robot."""

    nickname: str
    raw_device: dict[str, Any]
    work_state: dict[str, Any]

    @property
    def clean_st(self) -> str | None:
        """Return cleaning/mowing status code."""
        value = self.work_state.get("cleanSt")
        return str(value).lower() if value is not None else None

    @property
    def charge_st(self) -> str | None:
        """Return charge status code."""
        value = self.work_state.get("chargeSt")
        return str(value).lower() if value is not None else None

    @property
    def station_st(self) -> str | None:
        """Return station status code."""
        value = self.work_state.get("stationSt")
        return str(value).lower() if value is not None else None

    @property
    def activity(self) -> str:
        """Map Open Platform status codes to lawn_mower activities."""
        clean = self.clean_st
        charge = self.charge_st

        if clean in CLEAN_ST_MOWING:
            return "mowing"
        if clean in CLEAN_ST_PAUSED or charge == CHARGE_ST_RETURN_PAUSED:
            return "paused"
        if charge == CHARGE_ST_RETURNING:
            return "returning"
        if charge in CHARGE_ST_DOCKED:
            return "docked"
        if clean == "h" or clean is None:
            if charge in CHARGE_ST_DOCKED or charge in (None, "i"):
                return "docked"
            return "paused"
        return "error"
