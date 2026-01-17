"""
Fire TV Remote Control Library

A Python library for discovering, pairing with, and controlling Fire TV devices
over the local network using the Fire TV Remote protocol.
"""

import json
import time
import uuid
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

import requests
import urllib3
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

# Suppress InsecureRequestWarning for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Constants
API_KEY = "0987654321"
DIAL_PORT = 8009
API_PORT = 8080
SERVICE_TYPE = "_amzn-fireTv._tcp.local."
DEFAULT_TIMEOUT = 5


class KeyAction(Enum):
    """Key action types for button presses."""
    DOWN = "keyDown"
    UP = "keyUp"


class ScanDirection(Enum):
    """Media scan/seek directions."""
    FORWARD = "forward"
    BACKWARD = "backward"


@dataclass
class FireTVDevice:
    """Represents a discovered Fire TV device."""
    name: str
    host: str
    port: int = API_PORT

    def __str__(self):
        return f"{self.name} ({self.host})"


@dataclass
class DeviceProperties:
    """Fire TV device properties and capabilities."""
    os_version: str
    platform_type: str
    turnstile_version: str
    epg_support: str
    power_support: str
    volume_support: str
    pfm: str


@dataclass
class App:
    """Represents an app on the Fire TV."""
    app_id: str
    name: str
    is_installed: bool
    is_shortcut: bool
    icon_url: str
    launch_intent: str


class FireTVListener(ServiceListener):
    """Zeroconf listener for Fire TV device discovery."""

    def __init__(self, callback: Optional[Callable[[FireTVDevice], None]] = None):
        self.devices: list[FireTVDevice] = []
        self.callback = callback

    def add_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        info = zc.get_service_info(service_type, name)
        if info:
            addresses = info.parsed_addresses()
            if addresses:
                device = FireTVDevice(
                    name=name.replace("._amzn-fireTv._tcp.local.", ""),
                    host=addresses[0],
                    port=API_PORT
                )
                self.devices.append(device)
                if self.callback:
                    self.callback(device)

    def remove_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        pass

    def update_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        pass


def discover_devices(timeout: float = 5.0,
                     callback: Optional[Callable[[FireTVDevice], None]] = None) -> list[FireTVDevice]:
    """
    Discover Fire TV devices on the local network.

    Args:
        timeout: How long to wait for discovery (seconds)
        callback: Optional callback called when a device is found

    Returns:
        List of discovered FireTVDevice objects
    """
    zeroconf = Zeroconf()
    listener = FireTVListener(callback)

    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
    time.sleep(timeout)

    zeroconf.close()
    return listener.devices


class FireTV:
    """
    Fire TV remote control client.

    Usage:
        # Connect to a known device
        tv = FireTV("192.168.1.100")

        # Or discover and connect
        devices = discover_devices()
        tv = FireTV(devices[0].host)

        # Pair with PIN
        tv.request_pin("My Remote")
        pin = input("Enter PIN shown on TV: ")
        tv.verify_pin(pin)

        # Control the device
        tv.home()
        tv.navigate_down()
        tv.select()
    """

    def __init__(self, host: str, port: int = API_PORT, token: Optional[str] = None):
        """
        Initialize Fire TV client.

        Args:
            host: IP address of the Fire TV device
            port: API port (default 8080)
            token: Pre-existing client token for reconnection
        """
        self.host = host
        self.port = port
        self.dial_port = DIAL_PORT
        self.token = token
        self.session = requests.Session()
        self.session.verify = False  # Accept self-signed certificates
        self.session.headers.update({
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "*/*",
            "x-api-key": API_KEY,
            "User-Agent": "FireTV-Python/1.0"
        })

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}"

    @property
    def dial_url(self) -> str:
        return f"http://{self.host}:{self.dial_port}"

    @property
    def is_paired(self) -> bool:
        return self.token is not None

    def _request(self, method: str, path: str, authenticated: bool = True,
                 json_data: Optional[dict] = None, timeout: int = DEFAULT_TIMEOUT) -> dict:
        """Make an API request."""
        url = f"{self.base_url}{path}"
        headers = {}

        if authenticated and self.token:
            headers["x-client-token"] = self.token

        headers["x-amzn-request-id"] = str(uuid.uuid4())

        response = self.session.request(
            method, url, headers=headers, json=json_data, timeout=timeout
        )
        response.raise_for_status()

        if response.content:
            return response.json()
        return {}

    # === Authentication ===

    def request_pin(self, friendly_name: str = "Python Remote") -> bool:
        """
        Request a PIN to be displayed on the Fire TV.

        Args:
            friendly_name: Name to identify this remote

        Returns:
            True if PIN display was requested successfully
        """
        result = self._request(
            "POST",
            "/v1/FireTV/pin/display",
            authenticated=False,
            json_data={"friendlyName": friendly_name}
        )
        return result.get("description") == "OK"

    def verify_pin(self, pin: str) -> bool:
        """
        Verify the PIN shown on the TV screen.

        Args:
            pin: 4-digit PIN shown on TV

        Returns:
            True if PIN was verified, token is stored automatically
        """
        result = self._request(
            "POST",
            "/v1/FireTV/pin/verify",
            authenticated=False,
            json_data={"pin": pin}
        )
        token = result.get("description", "")
        if token:
            self.token = token
            return True
        return False

    # === Device Information ===

    def get_status(self) -> dict:
        """Get basic device status."""
        return self._request("GET", "/v1/FireTV/status")

    def get_properties(self) -> DeviceProperties:
        """Get detailed device properties."""
        data = self._request("GET", "/v1/FireTV/properties")
        return DeviceProperties(
            os_version=data.get("osVersion", ""),
            platform_type=data.get("platformType", ""),
            turnstile_version=data.get("turnstileVersion", ""),
            epg_support=data.get("epgSupport", ""),
            power_support=data.get("powerSupport", ""),
            volume_support=data.get("volumeSupport", ""),
            pfm=data.get("pfm", "")
        )

    def get_capabilities(self) -> dict:
        """Get device capability flags."""
        return self._request("GET", "/v1/FireTV2")

    # === Applications ===

    def get_apps(self) -> list[App]:
        """Get list of available apps."""
        data = self._request("GET", "/v1/FireTV/appsV2")
        return [
            App(
                app_id=app.get("appId", ""),
                name=app.get("name", ""),
                is_installed=app.get("isInstalled", False),
                is_shortcut=app.get("isShortcutApp", False),
                icon_url=app.get("tvIconArt", ""),
                launch_intent=app.get("appShortcutLaunchIntent", "")
            )
            for app in data
        ]

    def launch_app_dial(self, app_name: str = "FireTVRemote") -> bool:
        """
        Launch an app via DIAL protocol.

        Args:
            app_name: DIAL app name to launch

        Returns:
            True if app was launched
        """
        url = f"{self.dial_url}/apps/{app_name}"
        response = self.session.post(url, headers={"Content-Type": "text/plain"}, data="")
        return response.status_code == 201

    # === Keyboard ===

    def get_keyboard_state(self) -> dict:
        """Get current keyboard state."""
        return self._request("GET", "/v1/FireTV/keyboard")

    # === Navigation Controls ===

    def _send_action(self, action: str, key_action: Optional[KeyAction] = None) -> bool:
        """Send a navigation action."""
        json_data = None
        if key_action:
            json_data = {"keyActionType": key_action.value}

        result = self._request("POST", f"/v1/FireTV?action={action}", json_data=json_data)
        return result.get("description") == "OK"

    def _send_key(self, action: str) -> bool:
        """Send a key press (down + up)."""
        self._send_action(action, KeyAction.DOWN)
        return self._send_action(action, KeyAction.UP)

    def navigate_up(self) -> bool:
        """Navigate up."""
        return self._send_key("dpad_up")

    def navigate_down(self) -> bool:
        """Navigate down."""
        return self._send_key("dpad_down")

    def navigate_left(self) -> bool:
        """Navigate left."""
        return self._send_key("dpad_left")

    def navigate_right(self) -> bool:
        """Navigate right."""
        return self._send_key("dpad_right")

    def select(self) -> bool:
        """Press select/OK button."""
        return self._send_key("select")

    def back(self) -> bool:
        """Press back button."""
        return self._send_action("back")

    def home(self) -> bool:
        """Press home button."""
        return self._send_action("home")

    def menu(self) -> bool:
        """Press menu button."""
        return self._send_action("menu")

    # Aliases for convenience
    up = navigate_up
    down = navigate_down
    left = navigate_left
    right = navigate_right
    ok = select
    enter = select

    # === Text Input ===

    def send_text(self, text: str) -> bool:
        """
        Send text input to the device.

        Args:
            text: Text to send (sent character by character)

        Returns:
            True if all characters were sent successfully
        """
        for char in text:
            result = self._request("POST", "/v1/FireTV/text", json_data={"text": char})
            if result.get("description") != "OK":
                return False
        return True

    def send_char(self, char: str) -> bool:
        """Send a single character."""
        result = self._request("POST", "/v1/FireTV/text", json_data={"text": char})
        return result.get("description") == "OK"

    # === Media Controls ===

    def play_pause(self) -> bool:
        """Toggle play/pause."""
        result = self._request("POST", "/v1/media?action=play")
        return result.get("description") == "OK"

    def seek(self, direction: ScanDirection = ScanDirection.FORWARD,
             seconds: int = 10, speed: int = 1) -> bool:
        """
        Seek through media.

        Args:
            direction: FORWARD or BACKWARD
            seconds: Number of seconds to seek
            speed: Playback speed
        """
        result = self._request(
            "POST",
            "/v1/media?action=scan",
            json_data={
                "direction": direction.value,
                "durationInSeconds": str(seconds),
                "speed": str(speed)
            }
        )
        return result.get("description") == "OK"

    def fast_forward(self, seconds: int = 10) -> bool:
        """Fast forward by specified seconds."""
        return self.seek(ScanDirection.FORWARD, seconds)

    def rewind(self, seconds: int = 10) -> bool:
        """Rewind by specified seconds."""
        return self.seek(ScanDirection.BACKWARD, seconds)


# Convenience function for quick connection
def connect(host: str, token: Optional[str] = None) -> FireTV:
    """
    Create a FireTV connection.

    Args:
        host: IP address of Fire TV device
        token: Optional pre-existing auth token

    Returns:
        FireTV client instance
    """
    return FireTV(host, token=token)


if __name__ == "__main__":
    # Example usage
    print("Discovering Fire TV devices...")
    devices = discover_devices(timeout=3)

    if devices:
        print(f"\nFound {len(devices)} device(s):")
        for i, device in enumerate(devices):
            print(f"  {i+1}. {device}")
    else:
        print("No devices found. Make sure Fire TV is on and connected to the same network.")
