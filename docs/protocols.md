# Description of used protocols

## Unsolicited sequences (mode "collect" of clients)

Viessmann E3 devices broadcast data point values on the CAN bus unsolicited,
whenever a value changes, without any prior request.
The format is similar to the response of a UDS ReadDataByIdentifier service,
but uses a different length encoding and does not require a flow-control
handshake.

---

### CAN-ID

Each E3 device transmits on a fixed CAN-ID:

| Device | CAN-ID |
|---|---|
| Vitocharge VX3 | `0x451` |
| Vitocal 250 (internal bus and connected systems) | `0x693` |

---

### Frame types

Every CAN frame is exactly 8 bytes.

**First Frame (FF)** — marks the start of a new data point transmission:

```
Byte 0:    0x21          (always, identifies the start of a sequence)
Byte 1:    DID_LOW       (low byte of the Data Identifier)
Byte 2:    DID_HIGH      (high byte of the Data Identifier)
Byte 3:    length code   (see length encoding below)
Byte 4+:   payload       (start position depends on length code)
```

**Continuation Frame (CF)** — carries the remaining payload bytes:

```
Byte 0:    sequence byte  (starts at 0x22, increments with each frame,
                           wraps 0x2F → 0x20)
Byte 1–7:  payload continuation
```

The last frame is padded to 8 bytes.

---

### Length encoding

The length code in byte 3 of the First Frame encodes both payload length and
frame type:

| Byte 3 (`v3`) | Byte 4 (`v4`) | Type | Payload length | Payload starts at |
|---|---|---|---|---|
| `0xB1`–`0xB4` | any | Single Frame | `v3 − 0xB0` (1–4 bytes) | Byte 4 |
| `0xB5`–`0xBF` | any | Multi Frame | `v3 − 0xB0` (5–15 bytes) | Byte 4 |
| `0xB0` | ≠ `0xC1` | Multi Frame | `v4` (16–255 bytes) | Byte 5 |
| `0xB0` | `0xC1` | Multi Frame | Byte 5 (`v5`) | Byte 6 |

The `0xC1` escape in the last row is used when the payload length value itself
would equal `0xB5` or `0xC1`, to avoid ambiguity with those special byte
values. In practice this has been observed for a payload length of `0xB5`
(181 bytes).

---

### Multi-frame sequence

No flow control is required. The device sends all frames back-to-back:

```
Device                          Listener
  |                               |
  |── First Frame ───────────────>|
  |── Continuation Frame 1 ──────>|
  |── Continuation Frame 2 ──────>|
  |           …                   |
  |── Continuation Frame n ──────>|   ← last frame, padded to 8 bytes
```

---

### Complete examples

**Single Frame** — DID `0x09BE`, payload length 4:

```
#        seq  DID       len  payload
can0  693 [8]  21  BE 09  B4  95 0E 00 00
```
`v3 = 0xB4` → length = `0xB4 − 0xB0` = 4. Payload: `95 0E 00 00`.

---

**Multi Frame** — DID `0x011A`, payload length 9:

```
#             seq  DID len payload ...
can0  693 [8]  21 1A 01 B9 90 01 D4 00
can0  693 [8]  22 E5 01 82 01 00 55 55
```
`v3 = 0xB9` → length = 9. Payload bytes 1–4 start at byte 4 of frame 1,
bytes 5–9 follow in frame 2 (last 2 bytes are padding).

---

**Multi Frame** — DID `0x0224`, payload length 24 (`0x18`):

```
#             seq  DID len v4 payload ...
can0  693 [8]  21 24 02 B0 18 55 00 00
can0  693 [8]  22 00 1A 03 00 00 5F 0A
can0  693 [8]  23 00 00 38 0F 00 00 9B
can0  693 [8]  24 32 00 00 57 5E 00 00
```
`v3 = 0xB0`, `v4 = 0x18` (≠ `0xC1`) → length = 24. Payload starts at byte 5
of frame 1.

---

**Multi Frame** — DID `0x0509`, payload length 181 (`0xB5`), using `0xC1` escape:

```
#             seq  DID len esc len2 payload ...
can0  693 [8]  21 09 05 B0 C1  B5   00 00
can0  693 [8]  22 00 00 00 00 00 00 00
can0  693 [8]  23 00 00 00 00 00 00 00
  ... (26 frames total) ...
can0  693 [8]  2B 00 00 00 00 55 55 55
```
`v3 = 0xB0`, `v4 = 0xC1` (escape) → length = `v5 = 0xB5` = 181. Payload
starts at byte 6 of frame 1. Last frame padded with `0x55`.

---

### Receiver implementation checklist

1. Listen on the device's CAN-ID for frames with byte 0 = `0x21` — this
   marks the start of a new data point.
2. Extract the DID from bytes 1–2: `DID = byte1 + 256 × byte2` (little-endian).
3. Decode the length code in byte 3 using the table above to determine payload
   length and start position.
4. **Single Frame:** extract the payload directly and decode the data point.
5. **Multi Frame:** record the expected next sequence byte (`0x22`), then
   collect Continuation Frames until the full payload has been received.
   - With each frame, verify byte 0 matches the expected sequence value.
     If not, a frame was lost — discard the incomplete message.
   - Increment the expected sequence byte after each frame; wrap `0x2F → 0x20`.
6. Discard padding bytes beyond the declared payload length in the last frame.

---

# UDS – ReadDataByIdentifier and WriteDataByIdentifier

UDS (Unified Diagnostic Services, ISO 14229) is a diagnostic protocol used in
automotive ECUs.  This document covers the two services relevant for reading
and writing data points on Viessmann E3 devices.

UDS is **not** used by E3onCAN but by open3e.

---

## Transport layer – ISO-TP (ISO 15765-2)

UDS messages are not sent as raw bytes on the CAN bus.  They are wrapped in
**ISO-TP** frames, which handle segmentation and reassembly for payloads longer
than 7 bytes.

### CAN-ID mapping

| Direction | CAN-ID |
|---|---|
| Client → Device (request) | `tx` address of the device, e.g. `0x680` |
| Device → Client (response) | `tx + 0x10`, e.g. `0x690` |

### Frame types

Every CAN frame is exactly 8 bytes.

**Single Frame (SF)** – payload fits in one frame (≤ 7 UDS bytes):

```
Byte 0:   0x0n   (n = payload length, 1–7)
Byte 1–n: UDS payload
Byte n+1–7: padding (0xCC)
```

**First Frame (FF)** – first segment of a longer message:

```
Byte 0:   0x1H   (H = high nibble of total payload length)
Byte 1:   0xLL   (low byte of total payload length, max 4095)
Byte 2–7: first 6 bytes of UDS payload
```

**Flow Control (FC)** – sent by the receiver after an FF to authorise
transmission of the Consecutive Frames:

```
Byte 0:   0x30   (ContinueToSend)
Byte 1:   0x00   (block size = 0, send all)
Byte 2:   0x00   (separation time = 0 ms)
Byte 3–7: 0x00   (padding)
```

**Consecutive Frame (CF)** – subsequent segments:

```
Byte 0:   0x2n   (n = sequence number, starts at 1, wraps 15 → 0)
Byte 1–7: next 7 bytes of UDS payload
```

### Multi-frame exchange sequence

```
Client                          Device
  |                               |
  |── First Frame ───────────────>|
  |<── Flow Control ──────────────|
  |── Consecutive Frame 1 ───────>|
  |── Consecutive Frame 2 ───────>|
  |        …                      |
  |── Consecutive Frame n ───────>|   ← last frame, padded with 0xCC
  |                               |
  |<── [UDS response, same rules] |
```

---

## UDS message structure

After ISO-TP reassembly the raw UDS payload has this general structure:

```
Byte 0:   Service ID (SID)
Byte 1–2: Data Identifier (DID), big-endian (high byte first)
Byte 3+:  Data (for write requests and positive read responses)
```

A **negative response** always looks like:

```
Byte 0:   0x7F
Byte 1:   SID of the failed request
Byte 2:   Negative Response Code (NRC)
```

---

## Service 0x22 – ReadDataByIdentifier

### Request

```
[0x22] [DID_HIGH] [DID_LOW]
```

Example – read DID 256 (0x0100):

```
22 01 00
```

### Positive response

```
[0x62] [DID_HIGH] [DID_LOW] [DATA ...]
```

The response SID is always `request SID + 0x40`, so `0x22 + 0x40 = 0x62`.

Example – DID 256 returns 2 bytes:

```
62 01 00 CF 01
```

### Negative responses

| NRC | Hex | Meaning |
|---|---|---|
| serviceNotSupported | `0x11` | Service 0x22 not supported by this ECU |
| subFunctionNotSupported | `0x12` | Request too short or malformed |
| requestOutOfRange | `0x31` | DID is unknown to this ECU |

---

## Service 0x2E – WriteDataByIdentifier

### Request

```
[0x2E] [DID_HIGH] [DID_LOW] [DATA ...]
```

Example – write DID 268 (0x010C) with value `8C 01`:

```
2E 01 0C 8C 01
```

### Positive response

```
[0x6E] [DID_HIGH] [DID_LOW]
```

Note: the response does **not** echo the written value back.
To verify, issue a ReadDataByIdentifier request afterwards.

Example:

```
6E 01 0C
```

### Negative responses

| NRC | Hex | Meaning |
|---|---|---|
| serviceNotSupported | `0x11` | Service 0x2E not supported by this ECU |
| subFunctionNotSupported | `0x12` | Request too short or malformed |
| conditionsNotCorrect | `0x22` | DID is write-protected (see Service 77) |
| requestOutOfRange | `0x31` | DID is unknown to this ECU |
| securityAccessDenied | `0x33` | Write requires prior security access |

---

## Complete exchange example

Read DID 256 (0x0100) from the main device (tx = 0x680).
The value is 36 bytes, so the response spans multiple ISO-TP frames.

```
# Request (Single Frame, 3-byte UDS payload)
680  [8]  03 22 01 00 CC CC CC CC

# Response: First Frame (total UDS payload = 39 bytes: 3 header + 36 data)
690  [8]  10 27 62 01 00 3B 02 06

# Client sends Flow Control
680  [8]  30 00 00 00 00 00 00 00

# Consecutive Frames
690  [8]  21 00 47 00 FD 01 C3 08
690  [8]  22 01 00 03 00 F9 01 30
690  [8]  23 01 02 00 30 30 30 30
690  [8]  24 30 30 30 30 30 30 30
690  [8]  25 30 30 30 30 38 31 35
```

Reassembled UDS response payload:
```
62 01 00 3B 02 06 00 47 00 FD 01 C3 08 01 00 03
00 F9 01 30 01 02 00 30 30 30 30 30 30 30 30 30
30 30 30 38 31 35
```

---

## Client implementation checklist

**For reading:**
1. Build a 3-byte UDS request `[0x22, DID_HIGH, DID_LOW]`.
2. Wrap in an ISO-TP Single Frame and send on the device's `tx` CAN-ID.
3. Wait for a response on `tx + 0x10`.
4. If the first nibble of the first byte is `0x1` (First Frame), send a Flow
   Control frame immediately, then collect all Consecutive Frames.
5. Reassemble the UDS payload and check byte 0:
   - `0x62` → positive response, data starts at byte 3.
   - `0x7F` → negative response, NRC is in byte 2.

**For writing:**
1. Build the UDS request `[0x2E, DID_HIGH, DID_LOW, DATA...]`.
2. If the request is ≤ 7 bytes, send as a Single Frame.
   If longer, send as First Frame, wait for Flow Control, then send
   Consecutive Frames.
3. Wait for a response on `tx + 0x10`.
4. Check byte 0 of the reassembled response:
   - `0x6E` → write confirmed.
   - `0x7F` with NRC `0x22` → DID is protected; retry with Service 77.
   - `0x7F` with other NRC → write failed; see NRC table above.
5. Optionally verify the written value with a subsequent ReadDataByIdentifier.

**Sequence number wrap:** CF sequence numbers run 1 → 2 → … → 15 → 0 → 1 …
The wrap is at 15 → 0, not 15 → 1.

**Timeout:** If no Flow Control arrives within ~1 s after a First Frame, abort
the transmission.

---

# Energy Meters – E380 CA and E3100CB

Both Viessmann energy meters use a simple raw broadcast protocol: each data
point is transmitted as a single, self-contained 8-byte CAN frame with no
framing, segmentation, or flow control. The CAN-ID (E380) or a byte within
the frame (E3100CB) identifies the data point.

---

## E380 CA

### CAN-ID mapping

The E380 transmits one frame per data point on a dedicated CAN-ID. Up to two
meters can coexist on the same bus using different CAN addresses:

| CAN address | CAN-ID range | IDs |
|---|---|---|
| 97 (default) | `0x250`–`0x25D` | even IDs only |
| 98 | `0x250`–`0x25D` | odd IDs only |

### Frame structure

Every frame is exactly 8 bytes. All 8 bytes are payload — there is no header:

```
Byte 0–7:  payload  (encoding depends on the data point, see table below)
```

The CAN-ID directly identifies the data point.

### Data point reference

| CAN-ID (addr 97 / addr 98) | Data point | Payload encoding |
|---|---|---|
| `0x250` / `0x251` | Active Power L1, L2, L3, Total | 4 × Int16s (W) |
| `0x252` / `0x253` | Reactive Power L1, L2, L3, Total | 4 × Int16s (VA) |
| `0x254` / `0x255` | Current L1, L2, L3; cosPhi | 3 × Int16s (A) + cosPhi |
| `0x256` / `0x257` | Voltage L1, L2, L3; Frequency | 3 × Int16s (V) + Int16 (/100 → Hz) |
| `0x258` / `0x259` | Cumulated Import, Export | 2 × Float32 (/1000 → kWh) |
| `0x25A` / `0x25B` | Total Active Power, Total Reactive Power | 2 × Int32s (/10, W / VA) |
| `0x25C` / `0x25D` | Cumulated Import | Int32 (/100 → kWh) + 4 bytes unused |

### Payload encodings

All multi-byte integers are little-endian.

**Int16s** (signed, scale 1): two's complement, 2 bytes, unit as stated.

**Int32s** (signed, scale 10): two's complement, 4 bytes, divide by 10 for
physical value.

**Float32**: IEEE 754 single-precision float, 4 bytes, divide by 1000 for
physical value in kWh.

**cosPhi** (2 bytes, scale 100):
```
Byte 0:  sign indicator  (0x04 = negative, any other = positive)
Byte 1:  absolute value  (divide by 100 for physical value)
```

### Example

Active Power frame from meter at CAN address 97 (`0x250`):

```
can0  250   [8]  60 00  F7 FF  94 FF  FC FF
                 └─L1─┘ └─L2─┘ └─L3─┘ └Tot┘
```

Decoded (signed Int16, scale 1):
- L1   = `0x0060` = 96 W
- L2   = `0xFFF7` = −9 W
- L3   = `0xFF94` = −108 W
- Total = `0xFFFC` = −4 W

---

## E3100CB

### CAN-ID

The E3100CB always transmits on a single fixed CAN-ID:

| Direction | CAN-ID |
|---|---|
| E3100CB → bus | `0x569` |

### Frame structure

Every frame is exactly 8 bytes. Byte 3 acts as the data point discriminator;
bytes 4–7 carry the 4-byte payload. Bytes 0–2 are unused:

```
Byte 0–2:  unused / ignored
Byte 3:    data point index  (decimal, 01–17; forms the DID suffix)
Byte 4–7:  payload           (4 bytes, encoding depends on data point)
```

The logical DID is formed as `1385.<byte3>`, e.g. byte 3 = `0x04` → DID `1385.04`.

### Data point reference

| Byte 3 | DID | Data point | Payload encoding |
|---|---|---|---|
| `0x01` | 1385.01 | Cumulated Import | Float32 (/1000 → kWh) |
| `0x02` | 1385.02 | Cumulated Export | Float32 (/1000 → kWh) |
| `0x03` | 1385.03 | Operation State | State byte (see below) |
| `0x04` | 1385.04 | Active Power Total | Int16s (W) |
| `0x05` | 1385.05 | Reactive Power Total | Int16s (var) |
| `0x06` | 1385.06 | Current L1 (absolute) | Int16s (A) |
| `0x07` | 1385.07 | Voltage L1 | UInt32 (V) |
| `0x08` | 1385.08 | Active Power L1 | Int16s (W) |
| `0x09` | 1385.09 | Reactive Power L1 | Int16s (var) |
| `0x0A` | 1385.10 | Current L2 (absolute) | Int16s (A) |
| `0x0B` | 1385.11 | Voltage L2 | UInt32 (V) |
| `0x0C` | 1385.12 | Active Power L2 | Int16s (W) |
| `0x0D` | 1385.13 | Reactive Power L2 | Int16s (var) |
| `0x0E` | 1385.14 | Current L3 (absolute) | Int16s (A) |
| `0x0F` | 1385.15 | Voltage L3 | UInt32 (V) |
| `0x10` | 1385.16 | Active Power L3 | Int16s (W) |
| `0x11` | 1385.17 | Reactive Power L3 | Int16s (var) |

### Payload encodings

All multi-byte integers are little-endian.

**Int16s** (signed, scale 1): two's complement, 2 bytes (bytes 4–5 used,
bytes 6–7 unused).

**UInt32** (unsigned, scale 1): 4 bytes (bytes 4–7).

**Float32**: IEEE 754 single-precision float, 4 bytes (bytes 4–7), divide by
1000 for physical value in kWh.

**State byte** (byte 4 only):
```
0x00  →  +1  (supply, drawing from grid)
0x04  →  −1  (feed-in, exporting to grid)
other →   0  (undefined)
```

### Example

Active Power Total frame (DID 1385.04):

```
can0  569   [8]  XX XX XX  04  D0 07  00 00
                            │   └──────┘
                            │   payload (bytes 4–5)
                            └── data point index
```

Decoded (signed Int16, scale 1): `0x07D0` = 2000 W.
