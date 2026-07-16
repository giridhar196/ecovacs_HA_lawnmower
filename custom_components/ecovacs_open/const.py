"""Constants for the Ecovacs lawn mower integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ecovacs_open"

CONF_MODE: Final = "mode"
MODE_CLOUD: Final = "cloud"
MODE_OPEN: Final = "open"

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

CLEAN_ST_MOWING: Final = frozenset(
    {"s", "goposition", "findpet", "cruise", "buildmap"}
)
CLEAN_ST_PAUSED: Final = frozenset(
    {
        "p",
        "gopositionpause",
        "findpetpause",
        "cruisepause",
        "buildmappause",
    }
)
CHARGE_ST_DOCKED: Final = frozenset({"charging", "sc", "wc"})
CHARGE_ST_RETURNING: Final = "g"
CHARGE_ST_RETURN_PAUSED: Final = "gp"

SERVICE_START_ZONES: Final = "start_zones"
SERVICE_START_EDGE_TRIM: Final = "start_edge_trim"
SERVICE_REFRESH_ZONES: Final = "refresh_zones"

ATTR_AREA_IDS: Final = "area_ids"
