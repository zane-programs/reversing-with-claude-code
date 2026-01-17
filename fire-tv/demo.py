#!/usr/bin/env python3
"""
Fire TV Interactive Remote Demo

An interactive terminal-based remote control for Fire TV devices.
Uses keyboard input for real-time control.

Controls:
    Arrow Keys  - Navigate (Up/Down/Left/Right)
    Enter       - Select/OK
    Backspace   - Back
    H           - Home
    M           - Menu
    Space       - Play/Pause
    < / >       - Rewind / Fast Forward
    T           - Text input mode
    A           - List apps
    Q           - Quit
"""

import sys
import os
import tty
import termios
import select
from typing import Optional

from firetv import FireTV, discover_devices, FireTVDevice


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_header():
    """Print the remote control header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}         🔥 Fire TV Remote Control 🔥       {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════{Colors.RESET}\n")


def print_controls():
    """Print the control legend."""
    print(f"{Colors.BOLD}Controls:{Colors.RESET}")
    print(f"  {Colors.YELLOW}↑ ↓ ← →{Colors.RESET}  Navigate")
    print(f"  {Colors.YELLOW}Enter{Colors.RESET}    Select/OK")
    print(f"  {Colors.YELLOW}Backspace{Colors.RESET} Back")
    print(f"  {Colors.YELLOW}H{Colors.RESET}        Home")
    print(f"  {Colors.YELLOW}M{Colors.RESET}        Menu")
    print(f"  {Colors.YELLOW}Space{Colors.RESET}    Play/Pause")
    print(f"  {Colors.YELLOW}< / >{Colors.RESET}    Rewind / Fast Forward")
    print(f"  {Colors.YELLOW}T{Colors.RESET}        Text input mode")
    print(f"  {Colors.YELLOW}A{Colors.RESET}        List apps")
    print(f"  {Colors.YELLOW}Q{Colors.RESET}        Quit")
    print()


def get_key():
    """Get a single keypress from the terminal."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        # Check if input is available
        if select.select([sys.stdin], [], [], 0.1)[0]:
            ch = sys.stdin.read(1)
            # Handle escape sequences (arrow keys)
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'UP'
                    elif ch3 == 'B':
                        return 'DOWN'
                    elif ch3 == 'C':
                        return 'RIGHT'
                    elif ch3 == 'D':
                        return 'LEFT'
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None


def discover_and_select() -> Optional[FireTVDevice]:
    """Discover devices and let user select one."""
    print(f"{Colors.CYAN}Searching for Fire TV devices...{Colors.RESET}")

    devices = []

    def on_device_found(device: FireTVDevice):
        devices.append(device)
        print(f"  {Colors.GREEN}Found: {device.name} ({device.host}){Colors.RESET}")

    discovered = discover_devices(timeout=5, callback=on_device_found)

    if not discovered:
        print(f"\n{Colors.RED}No Fire TV devices found.{Colors.RESET}")
        print(f"{Colors.DIM}Make sure your Fire TV is on and connected to the same network.{Colors.RESET}")
        return None

    print(f"\n{Colors.BOLD}Select a device:{Colors.RESET}")
    for i, device in enumerate(discovered):
        print(f"  {Colors.YELLOW}{i + 1}.{Colors.RESET} {device.name} ({device.host})")

    while True:
        try:
            choice = input(f"\n{Colors.CYAN}Enter number (1-{len(discovered)}): {Colors.RESET}")
            idx = int(choice) - 1
            if 0 <= idx < len(discovered):
                return discovered[idx]
        except (ValueError, KeyboardInterrupt):
            pass
        print(f"{Colors.RED}Invalid selection.{Colors.RESET}")


def pair_device(tv: FireTV) -> bool:
    """Guide user through PIN pairing process."""
    print(f"\n{Colors.YELLOW}Pairing required...{Colors.RESET}")
    print(f"{Colors.CYAN}Requesting PIN display on Fire TV...{Colors.RESET}")

    if tv.request_pin("Python Remote"):
        print(f"{Colors.GREEN}PIN should now be displayed on your TV.{Colors.RESET}")
        pin = input(f"\n{Colors.BOLD}Enter the 4-digit PIN: {Colors.RESET}")

        if tv.verify_pin(pin):
            print(f"{Colors.GREEN}Paired successfully!{Colors.RESET}")
            print(f"{Colors.DIM}Token: {tv.token}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}Invalid PIN. Please try again.{Colors.RESET}")
            return False
    else:
        print(f"{Colors.RED}Failed to request PIN display.{Colors.RESET}")
        return False


def text_input_mode(tv: FireTV):
    """Enter text input mode for typing."""
    print(f"\n{Colors.YELLOW}Text Input Mode{Colors.RESET}")
    print(f"{Colors.DIM}Type text and press Enter to send. Press Enter on empty line to exit.{Colors.RESET}")

    while True:
        text = input(f"{Colors.CYAN}> {Colors.RESET}")
        if not text:
            print(f"{Colors.DIM}Exiting text mode.{Colors.RESET}")
            break

        if tv.send_text(text):
            print(f"{Colors.GREEN}Sent: {text}{Colors.RESET}")
        else:
            print(f"{Colors.RED}Failed to send text.{Colors.RESET}")


def list_apps(tv: FireTV):
    """List installed apps."""
    print(f"\n{Colors.YELLOW}Installed Apps:{Colors.RESET}")
    apps = tv.get_apps()
    installed = [app for app in apps if app.is_installed]

    for app in sorted(installed, key=lambda x: x.name):
        print(f"  {Colors.GREEN}•{Colors.RESET} {app.name}")
        print(f"    {Colors.DIM}{app.app_id}{Colors.RESET}")


def run_remote(tv: FireTV):
    """Main remote control loop."""
    clear_screen()
    print_header()
    print(f"{Colors.GREEN}Connected to: {tv.host}{Colors.RESET}")
    print(f"{Colors.DIM}Token: {tv.token[:16]}...{Colors.RESET}\n")
    print_controls()

    print(f"{Colors.BOLD}Ready! Press keys to control your Fire TV.{Colors.RESET}\n")

    while True:
        key = get_key()
        if key is None:
            continue

        action = None
        action_name = ""

        if key == 'UP':
            action = tv.up
            action_name = "↑ Up"
        elif key == 'DOWN':
            action = tv.down
            action_name = "↓ Down"
        elif key == 'LEFT':
            action = tv.left
            action_name = "← Left"
        elif key == 'RIGHT':
            action = tv.right
            action_name = "→ Right"
        elif key in ('\r', '\n'):
            action = tv.select
            action_name = "⏎ Select"
        elif key == '\x7f':  # Backspace
            action = tv.back
            action_name = "◄ Back"
        elif key.lower() == 'h':
            action = tv.home
            action_name = "⌂ Home"
        elif key.lower() == 'm':
            action = tv.menu
            action_name = "☰ Menu"
        elif key == ' ':
            action = tv.play_pause
            action_name = "▶ Play/Pause"
        elif key == '<' or key == ',':
            action = tv.rewind
            action_name = "◀◀ Rewind"
        elif key == '>' or key == '.':
            action = tv.fast_forward
            action_name = "▶▶ Fast Forward"
        elif key.lower() == 't':
            text_input_mode(tv)
            print_controls()
            continue
        elif key.lower() == 'a':
            list_apps(tv)
            continue
        elif key.lower() == 'q' or key == '\x03':  # Q or Ctrl+C
            print(f"\n{Colors.YELLOW}Goodbye!{Colors.RESET}")
            break
        else:
            # Unknown key
            continue

        if action:
            try:
                result = action()
                status = f"{Colors.GREEN}✓{Colors.RESET}" if result else f"{Colors.RED}✗{Colors.RESET}"
                print(f"  {status} {action_name}")
            except Exception as e:
                print(f"  {Colors.RED}✗ {action_name} - Error: {e}{Colors.RESET}")


def main():
    """Main entry point."""
    clear_screen()
    print_header()

    # Check for direct IP argument
    if len(sys.argv) > 1:
        host = sys.argv[1]
        token = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"{Colors.CYAN}Connecting to {host}...{Colors.RESET}")
        tv = FireTV(host, token=token)
    else:
        # Discover devices
        device = discover_and_select()
        if not device:
            return

        print(f"\n{Colors.CYAN}Connecting to {device.name}...{Colors.RESET}")
        tv = FireTV(device.host)

    # Check if already paired or need to pair
    if not tv.is_paired:
        # Try to get status to check connection
        try:
            tv.get_status()
        except Exception as e:
            print(f"{Colors.RED}Connection failed: {e}{Colors.RESET}")
            return

        # Need to pair
        if not pair_device(tv):
            return

    # Run the remote
    try:
        run_remote(tv)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")


if __name__ == "__main__":
    main()
