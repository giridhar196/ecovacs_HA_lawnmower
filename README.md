# Ecovacs Open Lawn Mower

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=giridhar196&repository=ecovacs_HA_lawnmower&category=integration)
[![Open your Home Assistant instance and start setting up Ecovacs Open.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ecovacs_open)

Home Assistant custom integration for Ecovacs robotic lawn mowers using the official [Ecovacs Open Platform](https://open.ecovacs.com) API.

## Install (HACS)

1. Make sure [HACS](https://hacs.xyz) is installed.
2. Click **Add repository to HACS** below (or add this repo manually as category **Integration**):

   [![Add repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=giridhar196&repository=ecovacs_HA_lawnmower&category=integration)

3. Search for **Ecovacs Open Lawn Mower** in HACS and install it.
4. Restart Home Assistant.
5. Click **Add Integration** below (or Settings → Devices & services → Add integration → **Ecovacs Open**):

   [![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ecovacs_open)

6. Enter your Open Platform API key (AK) and region.

## Manual install

Copy `custom_components/ecovacs_open` into `/config/custom_components/`, restart Home Assistant, then use the Add Integration button above.

## Setup

1. Open [Ecovacs Open Platform](https://open.ecovacs.com) (China: [open.ecovacs.cn](https://open.ecovacs.cn))
2. Create a server API key (AK) and authorize your mower
3. In Home Assistant, add the integration and paste the AK

| Account region | API URL |
| --- | --- |
| Outside Mainland China | `https://open.ecovacs.com` |
| Mainland China | `https://open.ecovacs.cn` |

## Features

- Config flow with API key + region
- Discovers robots on your Open Platform account
- `lawn_mower` entity: start / pause / dock
- Sensors for mow, charge, and station status

## License

MIT
