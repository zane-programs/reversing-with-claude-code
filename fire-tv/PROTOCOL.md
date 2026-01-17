# Fire TV Remote Protocol Documentation

This document describes the HTTP-based protocol used by the Amazon Fire TV Remote iOS app to communicate with Fire TV devices on the local network.

## Overview

Fire TV devices expose two HTTP services for remote control:
- **Port 8009**: DIAL (Discovery and Launch) protocol for app launching
- **Port 8080**: Fire TV Remote API for device control

## Discovery

Fire TV devices advertise themselves via mDNS/Zeroconf with the service type `_amzn-fireTv._tcp.local.`.

## Authentication

### Step 1: Display PIN on TV

Request a PIN to be displayed on the Fire TV screen:

```http
POST /v1/FireTV/pin/display HTTP/1.1
Host: <device-ip>:8080
Content-Type: application/json; charset=utf-8
x-api-key: 0987654321

{"friendlyName":"<client-name>"}
```

Response:
```json
{"description":"OK"}
```

### Step 2: Verify PIN

Submit the PIN shown on screen to authenticate:

```http
POST /v1/FireTV/pin/verify HTTP/1.1
Host: <device-ip>:8080
Content-Type: application/json; charset=utf-8
x-api-key: 0987654321

{"pin":"<4-digit-pin>"}
```

**Success Response** (returns client token):
```json
{"description":"NtuqAPiEeILpVJdLr9f2lA"}
```

**Failure Response** (wrong PIN):
```json
{"description":""}
```

### Using the Client Token

After successful authentication, include the token in all subsequent requests:

```http
x-client-token: <token-from-pin-verify>
```

## Required Headers

All requests to port 8080 require:

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json; charset=utf-8` |
| `x-api-key` | `0987654321` (static value) |
| `x-client-token` | Token from PIN verification (authenticated requests only) |

## Endpoints

### Device Information

#### GET /v1/FireTV/status

Returns basic device status.

```json
{
  "osVersion": "0030468475268",
  "platformType": "android",
  "turnstileVersion": "0.1.52452"
}
```

#### GET /v1/FireTV/properties

Returns device capabilities and properties.

```json
{
  "epgSupport": "Supported",
  "internalIntentSupport": "Supported",
  "osVersion": "0030468475268",
  "pfm": "ATVPDKIKX0DER",
  "platformType": "android",
  "powerSupport": "NotSupported",
  "ringMySupport": "NotSupported",
  "turnstileVersion": "0.1.52452",
  "volumeSupport": "NotSupported",
  "volumeTroubleshootingAction": "DisplayTroubleShooting"
}
```

#### GET /v1/FireTV2

Returns capability flags.

```json
{
  "isEpgSupported": true,
  "isInternalIntentSupported": true,
  "isPropertiesApiSupported": true,
  "isVolumeControlsSupported": false,
  "powerCapabilityLevelOfSupport": "NotSupported",
  "ringableRemoteCount": 0,
  "volumeCapabilityLevelOfSupport": "NotSupported"
}
```

### Applications

#### GET /v1/FireTV/appsV2

Returns list of available/installed applications.

```json
[
  {
    "appId": "com.netflix.ninja",
    "appShortcutLaunchIntent": "",
    "isInstalled": true,
    "isShortcutApp": false,
    "name": "Netflix",
    "tvIconArt": "https://m.media-amazon.com/images/I/416aTengF1L.png"
  }
]
```

### Keyboard State

#### GET /v1/FireTV/keyboard

Returns current keyboard state (for text input UI).

```json
{
  "mode": null,
  "state": "hidden",
  "text": null
}
```

### Navigation Controls

#### POST /v1/FireTV?action=\<action\>

Send navigation button presses.

**Available actions:**
- `dpad_up` - Navigate up
- `dpad_down` - Navigate down
- `dpad_left` - Navigate left
- `dpad_right` - Navigate right
- `select` - Select/OK button
- `back` - Back button
- `home` - Home button
- `menu` - Menu button

**For D-pad and Select (with key state):**
```http
POST /v1/FireTV?action=dpad_up HTTP/1.1
...

{"keyActionType":"keyDown"}
```

Key action types:
- `keyDown` - Key pressed
- `keyUp` - Key released

**For Home, Back, Menu (simple press):**
```http
POST /v1/FireTV?action=home HTTP/1.1
...

(empty body)
```

### Text Input

#### POST /v1/FireTV/text

Send text characters to the device (when keyboard is active).

```http
POST /v1/FireTV/text HTTP/1.1
...

{"text":"h"}
```

Text is sent one character at a time.

### Media Controls

#### POST /v1/media?action=play

Play/pause media playback.

```http
POST /v1/media?action=play HTTP/1.1
...

(empty body)
```

#### POST /v1/media?action=scan

Seek/scan through media.

```http
POST /v1/media?action=scan HTTP/1.1
...

{
  "direction": "forward",
  "durationInSeconds": "10",
  "speed": "1"
}
```

Parameters:
- `direction`: `"forward"` or `"backward"`
- `durationInSeconds`: Seek amount in seconds (as string)
- `speed`: Playback speed (as string)

## DIAL Protocol (Port 8009)

Fire TV also supports the DIAL protocol for launching apps.

### Launch FireTV Remote App

```http
POST /apps/FireTVRemote HTTP/1.1
Host: <device-ip>:8009
Content-Type: text/plain
Content-Length: 0
```

Response: `201 Created` with `Location` header pointing to running instance.

## Error Handling

The API returns standard HTTP status codes:
- `200 OK` - Success
- `201 Created` - Resource created (DIAL)
- `401 Unauthorized` - Invalid/missing client token
- `400 Bad Request` - Invalid request format

Success responses typically include:
```json
{"description":"OK"}
```

## Example Flow

1. **Discover** device via mDNS (`_amzn-fireTv._tcp.local.`)
2. **Request PIN** via `POST /v1/FireTV/pin/display`
3. **Verify PIN** via `POST /v1/FireTV/pin/verify` → receive client token
4. **Control device** with token in `x-client-token` header:
   - Navigation: `POST /v1/FireTV?action=select`
   - Text: `POST /v1/FireTV/text`
   - Media: `POST /v1/media?action=play`

## Security Notes

- The `x-api-key` value (`0987654321`) appears to be a static, hardcoded value
- Authentication is per-device via PIN pairing
- Client tokens should be persisted for reconnection
- All communication is unencrypted HTTP on the local network
