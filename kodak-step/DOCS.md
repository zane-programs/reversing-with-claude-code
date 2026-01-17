# KODAK STEP Printer Bluetooth Protocol Specification

## Overview

The KODAK STEP series of portable photo printers communicate with mobile devices over Bluetooth using a proprietary binary protocol. This specification covers the KODAK STEP, KODAK STEP SLIM, and Step Touch variants.

## Supported Devices

| Device Name | Bluetooth Name Pattern | Notes |
|-------------|----------------------|-------|
| KODAK STEP | `KODAK STEP` | Original model |
| KODAK STEP SLIM | `KODAK STEP SLIM` | Slim variant |
| Step Touch | `Step Touch` | Touch-enabled model |
| Step Touch 2.0 | `Kodak_Step_Touch_2.0` | Updated touch model |

---

## Bluetooth Connection

### Service Discovery

The printer uses the **Serial Port Profile (SPP)** over Bluetooth Classic.

| Parameter | Value |
|-----------|-------|
| UUID | `00001101-0000-1000-8000-00805F9B34FB` |
| Protocol | RFCOMM |
| Default Channel | 6 (for some legacy devices) |

### Connection Modes

- **Insecure RFCOMM**: Default connection mode (`createInsecureRfcommSocketToServiceRecord`)
- **Secure RFCOMM**: Used for specific device models (Xiaomi 2013022, Lenovo A820)
- **Fixed Channel**: Used on Android 4.0.x/4.1.x Samsung, HTC, Sony devices

### Connection Flow

1. Discover Bluetooth devices
2. Filter for devices with names matching KODAK STEP patterns
3. Cancel any ongoing discovery
4. Create RFCOMM socket using SPP UUID
5. Connect to device
6. Upon successful connection, start I/O threads

---

## Packet Structure

All packets are **fixed 34 bytes** in length.

### Packet Format

| Offset | Size | Name | Description |
|--------|------|------|-------------|
| 0 | 1 | Header[0] | Always `0x1B` (ESC) |
| 1 | 1 | Header[1] | Always `0x2A` ('*') |
| 2 | 1 | Header[2] | Always `0x43` ('C') |
| 3 | 1 | Header[3] | Always `0x41` ('A') |
| 4 | 1 | Reserved | Always `0x00` |
| 5 | 1 | Device Type | `0x00` = Standard, `0x02` = SLIM |
| 6 | 1 | Command | Primary command byte |
| 7 | 1 | SubCommand | Sub-command or direction byte |
| 8-33 | 26 | Payload | Command-specific data |

### Magic Header

```
Bytes: 1B 2A 43 41
ASCII: ESC * C A
```

### Device Type Byte (Offset 5)

| Value | Device |
|-------|--------|
| `0x00` | KODAK STEP / Step Touch |
| `0x02` | KODAK STEP SLIM |

---

## Commands Reference

### Command Byte Summary (Offset 6)

| Cmd | Name | Description |
|-----|------|-------------|
| `0x00` | Print Control | Print operations and status |
| `0x01` | Accessory/Transfer | Device info and data transfer control |
| `0x02` | Firmware | Firmware version and update control |
| `0x03` | Upgrade | Firmware upgrade status |
| `0x04` | Error | Error acknowledgment |
| `0x05` | Progress | Print progress updates |
| `0x07` | Battery | Battery level queries (legacy) |
| `0x08` | Device Name | Device name operations |
| `0x0A` | Sticker | Sticker management |
| `0x0C` | Border | Border/frame management |
| `0x0D` | Paper Type | Paper type queries |
| `0x0E` | Battery Level | Battery level queries |
| `0x10` | Auto Power Off | Power management |
| `0x11` | Upload | Image upload from device |

---

## Detailed Command Specifications

### Print Ready Request (Cmd: 0x00, Sub: 0x00)

Initiates a print job by specifying image size and copy count.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x00` | Print command |
| 7 | `0x00` | Print ready sub-command |
| 8 | Size[0] | Image size byte 0 (MSB) |
| 9 | Size[1] | Image size byte 1 |
| 10 | Size[2] | Image size byte 2 (LSB) |
| 11 | Copies | Number of copies (1-255) |
| 12-15 | `0x00` | Reserved |

**Image Size Encoding:**

The 24-bit image size is split across bytes 8-10 in big-endian order:
- Byte 8: `(size >> 16) & 0xFF`
- Byte 9: `(size >> 8) & 0xFF`
- Byte 10: `size & 0xFF`

### Print Status Responses (Cmd: 0x00)

| Sub | Name | Payload |
|-----|------|---------|
| `0x01` | Print Cancelled | - |
| `0x02` | Print Started | Byte 8: Current copy number |
| `0x03` | Print Finished | Byte 8: Error code (0 = success) |
| `0x04` | Print Count Response | Byte 8-11: Total prints |

---

### Get Accessory Info (Cmd: 0x01, Sub: 0x00)

Retrieves comprehensive device information.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x01` | Accessory command |
| 7 | `0x00` | Get info sub-command |

**Response Packet (Cmd: 0x01, Sub: 0x02):**

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 8 | 1 | Status | 0 = Success |
| 13 | 1 | Printer Version | Hardware revision |
| 17 | 1 | Error Code | Current error state |
| 18 | 1 | Total Prints | Lifetime print count |
| 19 | 1 | Print Mode | Current print mode |
| 20 | 1 | Battery Status | Battery percentage |
| 21 | 1 | Auto Exposure | Auto exposure setting |
| 22 | 1 | Auto Power Off | Power off timeout |
| 23-28 | 6 | MAC Address | Device MAC address |
| 29-31 | 3 | Firmware Version | Major.Minor.Patch |
| 32-34 | 3 | Hardware Version | Major.Minor.Patch |
| 35-36 | 2 | Max Payload Size | Maximum bulk transfer size |

**Firmware Version Decoding:**
```
Version = (Byte29 << 16) | (Byte30 << 8) | Byte31
String = "Byte29.Byte30.Byte31"
```

---

### Update Accessory Info (Cmd: 0x01, Sub: 0x01)

Updates device settings.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x01` | Accessory command |
| 7 | `0x01` | Update info sub-command |
| 8+ | Payload | Settings data to update |

---

### Start of Send Acknowledgment (Cmd: 0x01, Sub: 0x00, Response)

Printer indicates readiness to receive data.

**Response Byte 8 - Transfer Type:**

| Value | Type | Description |
|-------|------|-------------|
| `0x00` | Image | Ready for print image data |
| `0x01` | CNX Firmware | Ready for CNX firmware |
| `0x02` | Main Firmware | Ready for main firmware |
| `0x03` | Sticker Add | Ready for sticker thumbnail |
| `0x04` | Filter | Ready for filter data |
| `0x05` | Border Add | Ready for border thumbnail |
| `0x06` | Upload Ready | Ready for upload operation |
| `0x07` | Device Name | Ready for device name |
| `0x08` | Sticker Ready | Ready for sticker image |
| `0x09` | Border Ready | Ready for border image |
| `0x0A` | Upload | Upload in progress |
| `0x0B` | Upgrade | Ready for firmware upgrade data |
| `0x0C` | TMD | Ready for TMD firmware |

**Response Byte 9 - Error Code:**
- `0x00`: Success, proceed with transfer
- Non-zero: Error, see Error Codes section

---

### End of Received Acknowledgment (Cmd: 0x01, Sub: 0x01, Response)

Printer confirms data reception complete.

**Byte 8 - Transfer Type:** Same values as Start of Send Ack

---

### Firmware TMD Request (Cmd: 0x02, Sub: 0x04)

Requests firmware and TMD version information.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x02` | Firmware command |
| 7 | `0x04` | TMD version sub-command |

**For SLIM devices:** Set byte 5 to `0x02`

**Response (Cmd: 0x02, Sub: 0x05):**

| Offset | Field | Description |
|--------|-------|-------------|
| 5 | Printer Version | Hardware revision |
| 8 | FW Major | Firmware major version |
| 9 | FW Minor | Firmware minor version |
| 10 | FW Patch | Firmware patch version |
| 11-12 | CNX Version | CNX version (byte11*10 + byte12) |
| 13-14 | TMD Version | TMD version (byte13*10 + byte14) |

---

### Enter Firmware Update Mode (Cmd: 0x02, Sub: 0x06)

Puts device into firmware update mode.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x02` | Firmware command |
| 7 | `0x06` | Enter update mode |
| 8 | Type | Firmware type to update |

---

### Firmware Upgrade Ready (Cmd: 0x03, Sub: 0x00)

Initiates firmware transfer.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x03` | Upgrade command |
| 7 | `0x00` | Upgrade ready sub-command |
| 8 | Size[0] | Firmware size MSB |
| 9 | Size[1] | Firmware size middle byte |
| 10 | Size[2] | Firmware size LSB |
| 11 | Type | 1=TMD, 2=FW |

**Response (Cmd: 0x02, Sub: 0x00):**

| Offset | Field | Description |
|--------|-------|-------------|
| 8 | Type | Transfer type (1=TMD, 2=FW) |
| 9 | Error | Error code (0 = ready) |
| 10-11 | Payload Size | Maximum payload size per packet |

---

### Firmware Bulk Transfer (Cmd: 0x05, Sub: 0x00)

Transfers firmware data in chunks.

**Packet Structure:**

| Offset | Size | Value | Description |
|--------|------|-------|-------------|
| 0-5 | 6 | Header | Standard header |
| 6 | 1 | `0x05` | Bulk transfer command |
| 7 | 1 | `0x00` | Data sub-command |
| 8-9 | 2 | Size | Payload size in this packet |
| 10+ | N | Data | Firmware chunk data |

**Transfer Protocol:**
1. Send Firmware Upgrade Ready command
2. Wait for response with max payload size
3. Split firmware into chunks of (maxPayloadSize - 20) bytes
4. Send each chunk with 100ms delay between packets
5. Continue until all data transferred

---

### Upgrade Status (Cmd: 0x03, Sub: 0x02)

**Response Byte 8:**

| Value | Status |
|-------|--------|
| `0x00` | Upgrade started |
| `0x01` | Upgrade completed successfully |
| `0x02` | Upgrade failed |

---

### Error Message Acknowledgment (Cmd: 0x04)

Used to acknowledge errors or indicate printer ready state.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x04` | Error command |
| 7 | `0x00` | Error ack sub-command |
| 8 | Error | Error code being acknowledged |

**Response (Cmd: 0x04, Sub: 0x00):**
- Byte 8 = `0x00`: Printer ready, send image data
- Byte 8 != 0: Error occurred, see Error Codes

---

### Print Progress (Cmd: 0x05)

**Response Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 8 | Progress | Print progress percentage (0-100) |

---

### Get Battery Level (Cmd: 0x0E, Sub: 0x00)

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x0E` | Battery command |
| 7 | `0x00` | Get level sub-command |

**Response (Cmd: 0x0F):**

| Offset | Value | Description |
|--------|-------|-------------|
| 8 | Level | Battery percentage (0-100) |

---

### Get/Set Sticker (Cmd: 0x0A)

**Get Stickers (Sub: 0x00):**

Request installed sticker list.

**Add Sticker (Sub: 0x02):**

| Offset | Value | Description |
|--------|-------|-------------|
| 8 | Index Low | Sticker index low byte |
| 9 | Index High | Sticker index high byte |
| 10 | `0x04` | Sticker type flag |

**Sticker Ready (Sub: 0x03):**

Prepare to transfer sticker image.

| Offset | Value | Description |
|--------|-------|-------------|
| 8 | Index Low | Sticker index low byte |
| 9 | Index High | Sticker index high byte |
| 10-12 | Size | Image size (24-bit, big-endian) |

---

### Get/Set Border (Cmd: 0x0C)

**Get Borders (Sub: 0x00):**

Request installed border list.

**Add Border (Sub: 0x02):**

| Offset | Value | Description |
|--------|-------|-------------|
| 8 | Index Low | Border index low byte |
| 9 | Index High | Border index high byte |
| 10 | `0x02` | Border type flag |

**Border Ready (Sub: 0x03):**

Prepare to transfer border image.

| Offset | Value | Description |
|--------|-------|-------------|
| 8 | Index Low | Border index low byte |
| 9 | Index High | Border index high byte |
| 10-12 | Size | Image size (24-bit, big-endian) |

---

### Get Paper Type (Cmd: 0x0D, Sub: 0x00)

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x0D` | Paper type command |
| 7 | `0x00` | Get type sub-command |

**Response:**

| Offset | Value | Description |
|--------|-------|-------------|
| 8 | Type | Paper type identifier |

---

### Get Auto Power Off (Cmd: 0x10, Sub: 0x00)

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x10` | Auto power off command |
| 7 | `0x00` | Get setting sub-command |

**Response:**

| Offset | Value | Description |
|--------|-------|-------------|
| 8 | Setting | Power off timeout value |

**Auto Power Off Values:**

| Value | Timeout |
|-------|---------|
| `0x00` | Always On |
| `0x04` | 3 minutes |
| `0x08` | 5 minutes |
| `0x0C` | 10 minutes |

---

### Send Device Name (Cmd: 0x08, Sub: 0x00)

Sets the device's Bluetooth name.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x08` | Device name command |
| 7 | `0x00` | Send name sub-command |

After receiving Start of Send Ack with type `0x07`, send the device name as raw bytes.

---

### Get Print Count (Cmd: 0x00, Sub: 0x04)

Retrieves lifetime print count.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x00` | Print command |
| 7 | `0x04` | Get count sub-command |

**Response:**
Returns print count data in payload.

---

### Upload Process Complete (Cmd: 0x11, Sub: 0x01)

Signals completion of sticker/border upload.

**Request Packet:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0-5 | Header | Standard header |
| 6 | `0x11` | Upload command |
| 7 | `0x01` | Complete sub-command |

---

### Image Upload from Printer (Cmd: 0x11)

**Upload Ready (Sub: 0x00):**

Printer is sending image data.

| Offset | Field | Description |
|--------|-------|-------------|
| 9-11 | Size | Image size (24-bit) |

**Upload Request (Sub: 0x02):**

Printer requests to send data.

---

## Print Workflow

### Complete Print Sequence

1. **Send Print Ready Request** (Cmd: 0x00, Sub: 0x00)
   - Include image size and copy count

2. **Wait for Start of Send Ack** (Cmd: 0x01, Sub: 0x00)
   - Byte 8 should be `0x00` (image transfer type)
   - Byte 9 should be `0x00` (no error)

3. **Send Image Data**
   - Send JPEG image as raw bytes
   - No chunking required for print images

4. **Wait for Print Started** (Cmd: 0x00, Sub: 0x02)
   - Confirms printer received data and started printing

5. **Monitor Print Progress** (Cmd: 0x05)
   - Byte 8 contains progress percentage

6. **Wait for Print Finished** (Cmd: 0x00, Sub: 0x03)
   - Byte 8 = `0x00`: Success
   - Byte 8 != `0x00`: Error code

### Image Format

- **Format:** JPEG
- **Quality:** 70% compression recommended
- **Encoding:** Standard JPEG with no additional framing

---

## Firmware Update Workflow

### Update Sequence

1. **Get Current Version** (Cmd: 0x02, Sub: 0x04)
   - Retrieve current firmware/TMD versions

2. **Enter Update Mode** (Cmd: 0x02, Sub: 0x06)
   - Specify firmware type to update

3. **Send Upgrade Ready** (Cmd: 0x03, Sub: 0x00)
   - Include firmware size and type

4. **Wait for Response** (Cmd: 0x02, Sub: 0x00)
   - Get max payload size from bytes 10-11

5. **Bulk Transfer** (Cmd: 0x05, Sub: 0x00)
   - Send firmware in chunks
   - Delay 100ms between packets
   - Chunk size = maxPayloadSize - 20

6. **Monitor Upgrade Status** (Cmd: 0x03, Sub: 0x02)
   - Wait for completion or failure

### Firmware Types

| Value | Type | Description |
|-------|------|-------------|
| 1 | TMD | TMD firmware file |
| 2 | FW | Main firmware file |

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | Success / Image Processing Error | Operation succeeded or image error |
| 1 | Printer Busy | Printer is processing another job |
| 2 | Paper Jam | Paper is jammed in the printer |
| 3 | Out of Paper | No paper loaded |
| 4 | Paper Mismatch | Wrong paper type detected |
| 5 | Data Error | Data transmission error |
| 6 | Door Open | Cover/door is open |
| 7 | System Error | General system error |
| 8 | Battery Low | Battery level too low to print |
| 9 | Battery Fault | Battery malfunction |
| 10 | High Temperature | Printer too hot |
| 11 | Low Temperature | Printer too cold |
| 12 | Cooling Mode | Printer is cooling down |
| 13 | Transfer Cancel | Transfer was cancelled |
| 14 | Wrong Customer | Device authentication failure |
| 15 | Paper Feeding Failure | Paper failed to feed |
| 16 | Different Printer | Wrong printer type |
| -2 | Not Connected | Device not connected |

---

## Status Codes

### Printer Status

| Value | Status |
|-------|--------|
| 0 | Not Connected |
| 1 | Connected |
| 2 | Printing |
| 3 | Print Error |
| 4 | Connecting |
| 5 | Print Start |
| 6 | Print Finished |
| 11 | Auto Connected |
| 12 | Connection Failed |

---

## Timing and Delays

| Operation | Delay | Notes |
|-----------|-------|-------|
| Between bulk transfers | 100ms | Firmware update chunks |
| Operation timeout | 30 seconds | General operations |
| Print timeout | 9 seconds | During active printing |
| Reconnect check | 1 second | Status polling interval |
| Operation stale check | 5 seconds | For image receiving |

---

## Battery Management

### Thresholds

| Threshold | Value | Use Case |
|-----------|-------|----------|
| Low Battery Warning | 10% | General warning |
| Firmware Update Minimum | 20% | Required for updates |

### Battery Status in Accessory Info

The battery status byte indicates approximate percentage. Values are typically in the range 0-100.

---

## Implementation Notes

### Packet Construction Example

```
# Print Ready Request for 50KB image, 2 copies
Packet:
  [0] = 0x1B  # ESC
  [1] = 0x2A  # '*'
  [2] = 0x43  # 'C'
  [3] = 0x41  # 'A'
  [4] = 0x00  # Reserved
  [5] = 0x00  # Device type (standard)
  [6] = 0x00  # Print command
  [7] = 0x00  # Print ready
  [8] = 0x00  # Size MSB (50000 = 0x00C350)
  [9] = 0xC3  # Size middle
  [10] = 0x50 # Size LSB
  [11] = 0x02 # 2 copies
  [12-33] = 0x00  # Padding
```

### Size Encoding/Decoding

**Encoding (24-bit big-endian):**
```
byte[0] = (size >> 16) & 0xFF  # MSB
byte[1] = (size >> 8) & 0xFF   # Middle
byte[2] = size & 0xFF          # LSB
```

**Decoding:**
```
size = (byte[0] << 16) | (byte[1] << 8) | byte[2]
```

### Max Payload Size

The maximum payload size is reported by the printer during firmware update initialization. Typical values:

- Calculate chunk size as: `maxPayloadSize - 20`
- This accounts for packet header overhead

---

## Checksum

The protocol does **not** use checksums. Data integrity relies on the Bluetooth transport layer.

---

## Appendix A: Packet Quick Reference

### Request Packets

| Operation | Cmd | Sub | Key Payload |
|-----------|-----|-----|-------------|
| Print Ready | 0x00 | 0x00 | Size[3], Copies |
| Get Print Count | 0x00 | 0x04 | - |
| Get Accessory Info | 0x01 | 0x00 | - |
| Update Accessory Info | 0x01 | 0x01 | Settings data |
| Get Firmware Version | 0x02 | 0x04 | - |
| Enter FW Update | 0x02 | 0x06 | FW type |
| FW Upgrade Ready | 0x03 | 0x00 | Size[3], Type |
| Bulk Transfer | 0x05 | 0x00 | Size[2], Data |
| Get Device Name | 0x08 | 0x00 | - |
| Get Sticker | 0x0A | 0x00 | - |
| Add Sticker | 0x0A | 0x02 | Index, Type |
| Sticker Ready | 0x0A | 0x03 | Index, Size[3] |
| Get Border | 0x0C | 0x00 | - |
| Add Border | 0x0C | 0x02 | Index, Type |
| Border Ready | 0x0C | 0x03 | Index, Size[3] |
| Get Paper Type | 0x0D | 0x00 | - |
| Get Battery Level | 0x0E | 0x00 | - |
| Get Auto Power Off | 0x10 | 0x00 | - |
| Upload Complete | 0x11 | 0x01 | - |

### Response Packets

| Event | Cmd | Sub | Key Payload |
|-------|-----|-----|-------------|
| Print Cancelled | 0x00 | 0x01 | - |
| Print Started | 0x00 | 0x02 | Copy number |
| Print Finished | 0x00 | 0x03 | Error code |
| Print Count | 0x00 | 0x04 | Count data |
| Start Send Ack | 0x01 | 0x00 | Type, Error |
| End Receive Ack | 0x01 | 0x01 | Type |
| Accessory Info | 0x01 | 0x02 | Full device info |
| FW Version | 0x02 | 0x05 | Version data |
| Upgrade Status | 0x03 | 0x02 | Status code |
| Error Ack | 0x04 | 0x00 | Error code |
| Print Progress | 0x05 | - | Percentage |
| Sticker Response | 0x0A | 0x01 | Sticker data |
| Border Response | 0x0C | 0x01 | Border data |
| Paper Type | 0x0D | - | Type |
| Battery Level | 0x0F | - | Level |
| Auto Power Off | 0x10 | - | Setting |

---

## Appendix B: Connection State Machine

```
[Disconnected] ---(discover)---> [Discovering]
      |                               |
      |                          (device found)
      |                               |
      |                               v
      |                         [Connecting]
      |                               |
      |                          (success/fail)
      |                               |
      +-------(fail)--------<---------+
      |                               |
      |                          (success)
      |                               |
      v                               v
[Disconnected] <--(error)---- [Connected]
                                    |
                              (print request)
                                    |
                                    v
                              [Printing]
                                    |
                            (complete/error)
                                    |
                                    v
                              [Connected]
```

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2024 | Initial protocol specification |

---

*This specification was reverse-engineered from the KODAK STEP Prints Android application (com.kodak.steptouch.apk) for interoperability purposes.*
