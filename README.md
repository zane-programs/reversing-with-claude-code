# Reversing Everything with Claude Code

Companion repository for my talk on using Claude Code for reverse engineering. This repo contains protocol documentation, working libraries, and malware analysis from live demonstrations of Claude Code's capabilities in understanding undocumented systems.

## About the Talk

Claude Code is an agentic orchestration layer built on Claude models that exposes command-line capabilities, web search, and data connectors. While designed for software engineering, its ability to analyze captured traffic, decompile binaries, and reason about protocols makes it surprisingly effective for reverse engineering tasks.

The goal: reduce RE fatigue by letting LLMs do the "dirty work" of static analysis, protocol inference, and documentation generation.

## Repository Contents

### `Reversing Everything with Claude Code (Zane St. John).pdf`

The slide deck from the talk.

### `fire-tv/`

Reverse engineering of the Amazon Fire TV local control protocol. Claude Code analyzed mitmproxy captures to produce:

- `PROTOCOL.md` - Full specification of the undocumented HTTP API (ports 8009/8080)
- `firetv.py` - Python library implementing device discovery, pairing, and remote control
- `demo.py` - Interactive terminal-based remote control
- `FireTVDump.mitm` - Original network capture used for analysis

### `kodak-step/`

Reverse engineering of the Kodak STEP Touch portable Bluetooth photo printer. Contains:

- `DOCS.md` - Complete Bluetooth SPP protocol specification (34-byte packet format, command structures, print workflow)
- `com.kodak.steptouch.apk` - The Android companion app
- `decompiled/` - Decompiled APK source code and resources

### `projector-malware/`

Security analysis of pre-installed malware found on a cheap Android-based projector. Claude Code identified and documented:

- `FINDINGS.md` - Executive summary of threats and indicators of compromise
- `TECHNICAL_ANALYSIS.md` - Deep technical analysis of the malware components
- `apks/` - The malicious APK samples (silentsdk, eventuploadservice, expandsdk, storeos, htcotaupdate)
- `extracted/` - Decompiled resources and code

Key findings include a Remote Access Trojan capable of loading arbitrary code, detailed event logging/spyware, and ad injection components - all running with SYSTEM privileges.

### `washing-machine/`

Placeholder for Speed Queen laundry machine API analysis (not yet uploaded).

## Takeaways

- Keep scope narrow and targeted with specific goals
- Expose devices, protocols, and APIs via MCPs and CLIs
- Use to-do list generation, multi-agent workflows, and extended thinking
- Claude Code can produce working protocol documentation and libraries from raw traffic captures

## Author

Zane St. John - Stanford Class of '27, SymSys
