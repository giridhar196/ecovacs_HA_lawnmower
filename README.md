# Ecovacs Lawn Mower for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=giridhar196&repository=ecovacs_HA_lawnmower&category=integration)
[![Open your Home Assistant instance and start setting up Ecovacs Open.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ecovacs_open)

Custom Home Assistant integration for Ecovacs GOAT lawn mowers.

## Install

1. HACS → custom repository `https://github.com/giridhar196/ecovacs_HA_lawnmower` (Integration)
2. Install **Ecovacs Lawn Mower** / **Ecovacs Open Lawn Mower**
3. Restart Home Assistant
4. Add integration → **Ecovacs Lawn Mower**

## Connection modes

### 1) Ecovacs account (recommended — full features)

Uses the same cloud/MQTT path as the Ecovacs app and open-source projects (`deebot-client`).

Provides:

- Start / pause / dock mowing
- Battery, error, Wi-Fi
- **Cut direction**
- **Edge mowing** / border switches
- Services for **zone mowing** and **edge trim**

Login with the same email, password, and country as the Ecovacs Home app.

### 2) Open Platform API key (limited)

Uses [open.ecovacs.com](https://open.ecovacs.com). Only basic start / pause / dock + status. **No zones or trim.**

## Zone mowing & edge trim

Developer Tools → Services:

| Service | Purpose |
| --- | --- |
| `ecovacs_open.start_zones` | Mow zones (`area_ids` like `1,2`) |
| `ecovacs_open.start_edge_trim` | Border/edge trim for zones |
| `ecovacs_open.refresh_zones` | Request zone list from mower |

Zone IDs match the Ecovacs app map areas.

Example:

```yaml
service: ecovacs_open.start_zones
data:
  device_id: YOUR_DEVICE_ID
  area_ids: "1,2"
```

## Notes

- Open Platform cannot expose zones/trim; that requires account/MQTT (how goat-g1 / deebot-client do it).
- Some GOAT models need a matching `deebot-client` hardware profile. If your model is unsupported, open an issue with the model name from diagnostics.
- Unofficial community project; not affiliated with Ecovacs.

## License

MIT
