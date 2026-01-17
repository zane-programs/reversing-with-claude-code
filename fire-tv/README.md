# Fire TV Remote Control

A Python library and interactive remote for controlling Amazon Fire TV devices over your local network.

## Features

- **Device Discovery** - Automatically find Fire TV devices on your network via mDNS/Zeroconf
- **PIN Pairing** - Secure authentication using the same PIN method as the official app
- **Full Remote Control** - Navigation, media controls, and text input
- **App Listing** - View installed applications
- **Interactive Demo** - Terminal-based remote with keyboard controls

## Requirements

- Python 3.10+
- Fire TV device on the same local network
- Dependencies: `requests`, `zeroconf`

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install requests zeroconf
```

## Quick Start

### Interactive Remote

Run the interactive terminal remote:

```bash
./demo.py
```

Or connect directly to a known IP:

```bash
./demo.py 192.168.1.100
```

### Library Usage

```python
from firetv import FireTV, discover_devices

# Discover devices
devices = discover_devices(timeout=5)
print(f"Found: {devices}")

# Connect to a device
tv = FireTV("192.168.1.100")

# Pair (first time only)
tv.request_pin("My Remote")
pin = input("Enter PIN shown on TV: ")
tv.verify_pin(pin)

# Save the token for reconnection
print(f"Token: {tv.token}")

# Control the device
tv.home()
tv.navigate_down()
tv.select()
tv.send_text("Hello")
tv.play_pause()
```

## API Reference

### Discovery

```python
from firetv import discover_devices

# Find all Fire TV devices (blocking)
devices = discover_devices(timeout=5)

# With callback for each device found
def on_found(device):
    print(f"Found: {device.name} at {device.host}")

devices = discover_devices(timeout=5, callback=on_found)
```

### Connection & Pairing

```python
from firetv import FireTV

# Create client
tv = FireTV("192.168.1.100")

# Request PIN to be displayed on TV
tv.request_pin("My Remote Name")

# Verify PIN (returns True on success, stores token)
success = tv.verify_pin("1234")

# Reconnect with saved token
tv = FireTV("192.168.1.100", token="saved_token_here")
```

### Navigation Controls

```python
tv.navigate_up()    # or tv.up()
tv.navigate_down()  # or tv.down()
tv.navigate_left()  # or tv.left()
tv.navigate_right() # or tv.right()
tv.select()         # or tv.ok() or tv.enter()
tv.back()
tv.home()
tv.menu()
```

### Text Input

```python
# Send a string (character by character)
tv.send_text("Hello World")

# Send a single character
tv.send_char("A")
```

### Media Controls

```python
tv.play_pause()
tv.fast_forward(seconds=10)
tv.rewind(seconds=10)

# Advanced seek
from firetv import ScanDirection
tv.seek(direction=ScanDirection.FORWARD, seconds=30, speed=2)
```

### Device Information

```python
# Basic status
status = tv.get_status()

# Detailed properties
props = tv.get_properties()
print(f"Platform: {props.platform_type}")
print(f"OS Version: {props.os_version}")

# Capabilities
caps = tv.get_capabilities()
print(f"Volume supported: {caps['isVolumeControlsSupported']}")
```

### Applications

```python
# List all apps
apps = tv.get_apps()
for app in apps:
    if app.is_installed:
        print(f"{app.name}: {app.app_id}")

# Launch app via DIAL
tv.launch_app_dial("FireTVRemote")
```

## Interactive Demo Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Navigate |
| Enter | Select/OK |
| Backspace | Back |
| H | Home |
| M | Menu |
| Space | Play/Pause |
| < | Rewind 10s |
| > | Fast Forward 10s |
| T | Text input mode |
| A | List apps |
| Q | Quit |

## Protocol Documentation

See [PROTOCOL.md](PROTOCOL.md) for detailed documentation of the Fire TV Remote protocol.

## Troubleshooting

### Device not found

- Ensure Fire TV is powered on
- Verify both devices are on the same network/subnet
- Check firewall settings (ports 8009 and 8080 must be accessible)

### PIN verification fails

- Make sure to enter the PIN quickly before it expires
- The PIN is 4 digits shown on the TV screen

### Connection refused

- The Fire TV Remote service may need to be enabled
- Try restarting the Fire TV device

## Security Notes

- Authentication tokens should be stored securely
- All communication is unencrypted HTTP on the local network
- The static API key is hardcoded in the protocol

## License

MIT License - See LICENSE file for details.
