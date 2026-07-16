# Ecovacs Open Lawn Mower (Home Assistant)

Custom Home Assistant integration for Ecovacs robotic lawn mowers using the official [Ecovacs Open Platform](https://open.ecovacs.com) API.

## Features

- Config flow with API key (AK) + region
- Discovers robots bound to your Open Platform account
- `lawn_mower` entity: start / pause / dock
- Sensors for raw mow, charge, and station status codes

## Prerequisites

1. Open [Ecovacs Open Platform](https://open.ecovacs.com) (Mainland China: [open.ecovacs.cn](https://open.ecovacs.cn))
2. Sign in with your Ecovacs account
3. Create a server API key (AK)
4. Authorize the AK for your robot(s)

## Install

### Manual

1. Copy `custom_components/ecovacs_open` into your Home Assistant `config/custom_components/` folder
2. Restart Home Assistant
3. **Settings → Devices & services → Add integration → Ecovacs Open (Lawn Mower)**
4. Enter your AK and region

### HACS

Add this repository as a custom integration repository in HACS, install **Ecovacs Open Lawn Mower**, restart, then add the integration from the UI.

## Region

| Account region | API URL |
| --- | --- |
| Outside Mainland China | `https://open.ecovacs.com` |
| Mainland China | `https://open.ecovacs.cn` |

## API used

Same endpoints as the official Ecovacs MCP server:

| Action | Endpoint | Notes |
| --- | --- | --- |
| List robots | `GET /robot/deviceList` | `ak` query param |
| Control / status | `POST /robot/ctl` | JSON: `ak`, `nickName`, `cmd`, `act` |

Commands:

- Mow start / resume / pause / stop → `cmd=Clean`, `act=s|r|p|h`
- Dock → `cmd=Charge`, `act=go-start`
- Status → `cmd=GetWorkState`

## Notes

- The Open Platform API is shared with vacuum robots; mowing maps to the `Clean` command.
- Some older models return error `5009` for `GetWorkState`. Control may still work; status sensors stay empty.
- For account-login / MQTT deep integration (maps, zones), use Home Assistant’s built-in [Ecovacs](https://www.home-assistant.io/integrations/ecovacs/) integration instead.

## License

MIT
