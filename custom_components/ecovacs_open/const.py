"""Constants for the Ecovacs Open lawn mower integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ecovacs_open"

CONF_API_KEY: Final = "api_key"
CONF_API_URL: Final = "api_url"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

API_URL_WORLDWIDE: Final = "https://open.ecovacs.com"
API_URL_CHINA: Final = "https://open.ecovacs.cn"

ENDPOINT_DEVICE_LIST: Final = "robot/deviceList"
ENDPOINT_CTL: Final = "robot/ctl"

CMD_CLEAN: Final = "Clean"
CMD_CHARGE: Final = "Charge"
CMD_GET_WORK_STATE: Final = "GetWorkState"

ACT_START: Final = "s"
ACT_RESUME: Final = "r"
ACT_PAUSE: Final = "p"
ACT_STOP: Final = "h"
ACT_CHARGE_START: Final = "go-start"
ACT_CHARGE_STOP: Final = "stopGo"

# cleanSt values that mean the robot is actively working (mowing/cleaning).
CLEAN_ST_MOWING: Final = frozenset(
    {
        "s",
        "goposition",
        "findpet",
        "cruise",
        "buildmap",
    }
)

# cleanSt values that mean paused.
CLEAN_ST_PAUSED: Final = frozenset(
    {
        "p",
        "gopositionpause",
        "findpetpause",
        "cruisepause",
        "buildmappause",
    }
)

# chargeSt values that mean docked / charging.
CHARGE_ST_DOCKED: Final = frozenset(
    {
        "charging",
        "sc",
        "wc",
    }
)

CHARGE_ST_RETURNING: Final = "g"
CHARGE_ST_RETURN_PAUSED: Final = "gp"
