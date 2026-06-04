# Description of used protocols

# UDS – ReadDataByIdentifier and WriteDataByIdentifier

UDS (Unified Diagnostic Services, ISO 14229) is a diagnostic protocol used in
automotive ECUs.  This document covers the two services relevant for reading
and writing data points on Viessmann E3 devices.

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
| low nibble 1–4 | any | Single Frame | low nibble of `v3` (1–4 bytes) | Byte 4 |
| low nibble 5–F | any | Multi Frame | low nibble of `v3` (5–15 bytes) | Byte 4 |
| low nibble 0 | ≠ `0xC1` | Multi Frame | `v4` (16–255 bytes) | Byte 5 |
| low nibble 0 | `0xC1` | Multi Frame | Byte 5 (`v5`) | Byte 6 |

**Length encoding rule:** the payload length is always the **low nibble** of
byte 3 (`v3 & 0x0F`). The high nibble is irrelevant for length purposes;
byte 3 at this position is always a length code.
Observed high-nibble values include `0x8` and `0xB`; both encode the same
lengths (e.g. `0x82` and `0xB2` both mean 2 bytes).

Low nibble = 0 signals a two-byte length field: the actual length is in
byte 4 (`v4`), except when `v4 = 0xC1`, which is an escape byte — the true
length is then in byte 5 (`v5`). The `0xC1` escape avoids ambiguity when the
payload length value itself would equal `0xB5` or `0xC1`. In practice this
has been observed for a payload length of `0xB5` (181 bytes).

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
`v3 = 0xB4` → low nibble = 4 → length = 4. Payload: `95 0E 00 00`.

---

**Multi Frame** — DID `0x011A`, payload length 9:

```
#             seq  DID len payload ...
can0  693 [8]  21 1A 01 B9 90 01 D4 00
can0  693 [8]  22 E5 01 82 01 00 55 55
```
`v3 = 0xB9` → low nibble = 9 → length = 9. Payload bytes 1–4 start at byte 4
of frame 1, bytes 5–9 follow in frame 2 (last 2 bytes are padding).

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

## Service 77 (proprietary write protocol)

### Background

Service 77 is a Viessmann-proprietary write protocol discovered via reverse engineering. It operates in parallel with UDS on a dedicated CAN-ID pair and allows writing of data points that are protected against normal `WriteDataByIdentifier` (UDS service 0x2E).

Viessmann uses this mechanism to protect certain data points from accidental or unauthorised modification. When a client receives NRC `0x22` (conditionsNotCorrect) in response to a normal UDS write, it can retry the same write using Service 77 on the dedicated CAN-ID.

Both protocols share the same data store: a value written via Service 77 is immediately readable via UDS `ReadDataByIdentifier`.

### CAN-ID mapping

The Service 77 CAN-IDs are derived from the device's UDS address:

| | CAN-ID |
|---|---|
| Service 77 request  | `device_tx + 0x02`  (e.g. `0x682` for main device at `0x680`) |
| Service 77 response | `device_tx + 0x12`  (= request + `0x10`) |

### Transport layer

Service 77 uses the same ISO 15765-2 (ISO-TP) framing as UDS. The reassembled payload is described below.

### Request frame format

After ISO-TP reassembly the payload has this structure:

```
Byte 0:     0x77
Bytes 1–2:  [CTR_L] [CTR_H]
Bytes 3–5:  0x43 0x01 0x82
Bytes 6–7:  [DID_L] [DID_H]
Byte  8:    0xB0 + n
Bytes 9+:   [DATA ...]
```

| Field | Bytes | Description |
|---|---|---|
| Service ID | 1 | Always `0x77` |
| Session counter | 2 | 16-bit little-endian counter; monotonically increasing across all writes in a session (~0.35 increments/s), wraps at 0xFFFF |
| Client ID | 3 | Fixed bytes `43 01 82`; constant across all observed frames |
| DID | 2 | Data identifier, **little-endian** (low byte first) |
| Length code | 1 | Present only when the high nibble is ≥ `0x8` (observed: `0x8x` and `0xBx`). Low nibble = data length in bytes (e.g. `0x82` and `0xB2` both mean 2 bytes). Low nibble 0 means the next byte carries the length (≥ 16 bytes). **If the byte at this position has high nibble < `0x8`, it is not a length code — the remaining payload bytes including that byte are raw data** (observed for small data points, e.g. a 1-byte value of `0x2B`). |
| Data | n | New value for the data point, little-endian |

### Response frame format

Positive response:

```
[0x77] [CTR_L] [CTR_H] [0x44]
```

| Field | Bytes | Description |
|---|---|---|
| Service ID | 1 | Always `0x77` |
| Session counter | 2 | 16-bit LE counter **echoed from the request** (not the DID) |
| Confirmation byte | 1 | Always `0x44` (Viessmann-specific, no UDS equivalent) |

Negative response (reuses UDS encoding):

```
[0x7F] [0x77] [NRC]
```

| NRC | Meaning |
|---|---|
| `0x12` | Payload too short (subFunctionNotSupported) |
| `0x31` | DID not present in data store (requestOutOfRange) |

### Interaction with UDS WriteDataByIdentifier

The `service77` key in `devices.json` specifies a list of DIDs that are protected against normal UDS writes:

* A `WriteDataByIdentifier` (0x2E) request targeting a protected DID returns NRC `0x22` (conditionsNotCorrect) without modifying the data store.
* A Service 77 request targeting the same DID is accepted and the value is written normally.
* Service 77 accepts writes to **all** known DIDs, including unprotected ones.

### Example exchange

Write DID `0x044C` (decimal 1100) with 2-byte value `0x012C` on the main device (`tx = 0x680`).
Session counter at this point: `0x0042`.

The reassembled UDS payload is 11 bytes, so ISO-TP multi-frame is used:

```
# Client request on 0x682 (= 0x680 + 0x02):
#                   ISO-TP FF (len=11)
682  [8]  10 0B  77  42 00  43 01 82
#                ↑   ↑───↑  ↑──────↑
#                SID CTR   Client ID

#                   ISO-TP CF1
682  [8]  21  4C 04  B2  2C 01  CC CC
#             ↑────↑ ↑   ↑────↑
#             DID LE len  data LE

# Device sends Flow Control first (standard ISO-TP):
692  [8]  30 00 00 00 00 00 00 00

# Server response on 0x692 (= 0x682 + 0x10):
692  [8]  04  77  42 00  44  CC CC CC
#             ↑   ↑────↑  ↑
#             SID CTR     confirm=0x44
```

Notes:
- DID `0x044C` is transmitted as `4C 04` (LE), not `04 4C` (BE).
- The response echoes the session counter `42 00`, not the DID.
- `0xB2` indicates 2 data bytes (low nibble = 2). `0x82` is equally valid and observed on real hardware.

### Service 77 read

In addition to writes, a **read** variant has been observed on the Vitocharge
VX3 external CAN bus. The client requests the current value of a specific DID;
the device responds with the full data payload. The framing is standard ISO-TP
with Flow Control, identical to a write exchange.

#### Read request

After ISO-TP reassembly (always 8 bytes):

```
Byte 0:    0x77
Bytes 1–2: [CTR_L] [CTR_H]
Bytes 3–5: 0x41 0x01 0x82   (read-request marker)
Bytes 6–7: [DID_L] [DID_H]
```

No length code and no data follow — the request carries only the DID.

#### Read response

After ISO-TP reassembly:

```
Byte 0:    0x77
Bytes 1–2: [CTR_L] [CTR_H]   (echoed from request)
Bytes 3–5: 0x42 0x01 0x82   (read-response marker)
Bytes 6–7: [DID_L] [DID_H]  (echoed from request)
Byte  8:   length code       (same encoding as write request, see above)
Bytes 9+:  data
```

#### Example

Read DID `0x0509` (1289) from Vitocharge VX3 (`tx = 0x43F`, request channel
`0x441`, response channel `0x451`). The value is 181 bytes (0xB5), requiring
the `0xC1` length-code escape. CTR = `0x3634`.

```
# Client read request on 0x441 — ISO-TP total = 8 bytes
441  [8]  10 08  77  34 36  41 01 82
451  [8]  30 00 05 00 00 00 00 00       ← Flow Control from device
441  [8]  21  09 05  00 00 00 00 00
#         ↑─────↑
#         DID = 0x0509 LE

# Device read response on 0x451 — ISO-TP total = 192 bytes
451  [8]  10 C0  77  34 36  42 01 82
441  [8]  30 00 05 00 00 00 00 00       ← Flow Control from client
451  [8]  21  09 05  B0 C1 B5  00 00
#         ↑─────↑  ↑────────↑
#         DID echo  len=181 (0xC1 escape)
451  [8]  22 ... (26 frames total, SN wraps 0x2F → 0x20, padded with 0x55)
```

---

### Device-initiated Service 77 (CTR = 0x0000)

The device can initiate Service 77 frames toward the client, always with
session counter `0x0000`. Two distinct patterns have been observed:

**Pattern A — Cross-device synchronization (echo)**

When a client writes a value, the device immediately propagates that write to
all other known devices using the same CAN-ID offset. The payload (DID + data)
is identical to the client's write; only the counter is reset to zero.
Confirmed across multiple traces and DIDs (e.g. `0x01F8`, `0x044D`).

Example: client `0x682` writes DID `0x01F8`. Immediately after confirming,
device `0x692` pushes the same DID/data back to `0x682`, and simultaneously
`0x693` pushes the identical frame to `0x683`:

```
# Client write
682  10 17 77 0D 00 43 01 82   ← FF, CTR=0x000D
...
692  04 77 0D 00 44 55 55 55   ← confirm, CTR=0x000D ✓

# Immediate cross-device sync (CTR=0x0000 in both)
692  10 17 77 00 00 43 01 82   ← device pushes same DID back to 682
693  10 17 77 00 00 43 01 82   ← sibling device pushes to 683 simultaneously
```

**Pattern B — Related-value notification**

After processing a write, the device pushes back a set of related DIDs whose
values were affected by (or are logically associated with) the write. These
pushed DIDs are different from the written DID.

Example: client `0x441` writes DID `0x08B2` (2226). Before sending the
confirmation, device `0x451` pushes back four related DIDs:

| Pushed DID | Decimal | Data bytes |
|---|---|---|
| `0x0643` | 1603 | 4 |
| `0x069A` | 1690 | 17 |
| `0x0720` | 1824 | 16 |
| `0x072C` | 1836 | 4 |

The confirmation (`0x44`) for the original write arrives *after* all the
device-initiated pushes have been sent. This pattern is reproducible: the same
four DIDs are pushed on every write cycle to DID `0x08B2`, with data values
that reflect the current device state at the time of the push.

For large pushed payloads the ISO-TP sequence number wraps normally
(`0x2F → 0x20`). Payloads up to 123 bytes (19 CFs) have been observed for
device-initiated pushes on some DID/channel combinations.

**Short pushes (1-byte data, no length code prefix):** For data points with a
1-byte value whose byte representation has high nibble < `0x8`, the reassembled
S77 payload is exactly 9 bytes (8-byte header + 1 data byte) and the data byte
sits at position 8 without a preceding length code. Example:

```
# ISO-TP FF (total = 9 bytes)
692  [8]  10 09  77 00 00 43 01 82
# ISO-TP CF1 (need 3 more bytes: EF 06 2B)
692  [8]  21  EF 06  2B  55 55 55 55
#              ↑────↑  ↑
#              DID LE  data = 0x2B (43 decimal)
```

Reassembled: `77 00 00 43 01 82 EF 06 2B` — DID `0x06EF`, 1-byte value `0x2B`.
There is no length code byte; `0x2B` (high nibble `2` < `0x8`) is the value itself.

**Summary: how to identify device-initiated frames**

| Field | Client write | Device push |
|---|---|---|
| CTR | Running counter (≠ 0) | Always `0x0000` |
| Direction | REQUEST_CH → RESPONSE_CH | RESPONSE_CH → REQUEST_CH |
| DID | What the client wants to write | Echo of client's DID (Pattern A) or related DID (Pattern B) |

### Anomaly: 4-byte Service 77 frames

On multiple CAN-ID pairs, 4-byte Service 77 frames have been observed that
are too short to carry a DID or data:

```
681  04 77 C9 11 21 00 00 00   ← client-side (00 padding)
691  04 77 C9 11 22 55 55 55   ← device-side (55 padding), ~3 ms later

682  04 77 41 75 21 55 55 55   ← client-side (55 padding)
692  04 77 41 75 22 55 55 55   ← device-side (55 padding), 1 ms later

683  04 77 D4 11 21 00 00 00   ← client-side (00 padding)
693  04 77 D4 11 22 55 55 55   ← device-side (55 padding), 14 ms later

686  04 77 08 6F 21 CC CC CC   ← client-side (CC padding)
696  04 77 08 6F 22 55 55 55   ← device-side (55 padding), 1 ms later
```

Payload: `[0x77] [CTR_L] [CTR_H] [0x21]` (client) / `[0x77] [CTR_L] [CTR_H] [0x22]` (device)

Observations:

- `0x21` / `0x22` are consistent across all four channel pairs.
- The CTR in each pair is always the global session counter incremented by
  exactly 1 after the preceding write on that same channel (e.g. CTR=0x7540
  for a write, CTR=0x7541 for the 4-byte frame immediately after).
- The CAN padding byte on the **client** side is inconsistent: `0x00` on
  channels 681 and 683, `0x55` on 682, `0xCC` on 686. The device side always
  pads with `0x55`. This suggests the frames originate from different software
  components or firmware generations.
- These frames appear between write batches on all active channels, not only
  after specific writes.

**Hypothesis:** byte 3 = `0x21` / `0x22` is a session-level keepalive or
commit signal, sent by the client after each write (or write batch) to confirm
that no further writes are pending in this slot, with the device acknowledging.
The CTR+1 spacing supports this: the client "spends" one CTR value on the
keepalive before moving to the next write cycle.

### CAN-ID sharing and protocol disambiguation

CAN-IDs `0x451` (Vitocharge VX3) and `0x693` (Vitocal 250) are shared between
the Collect protocol and the Service 77 response channel. Both protocols produce
frames with sequence byte `0x21` as byte 0, making raw inspection ambiguous.

**Disambiguation rule (ISO-TP state tracking):**

A frame with byte 0 = `0x21` on `0x451` or `0x693` is:

- **Service 77 CF1** — if a First Frame (`0x1x`) from the same CAN-ID has
  been seen without a matching `0x21` CF1 consuming it yet.
- **Collect start frame (FF)** — if no ISO-TP FF is currently open for that
  CAN-ID.

An implementation must maintain one boolean flag per CAN-ID: "FF open".
Set it on `0x1x`; clear it on `0x21` (CF1 consumed) or `0x2x` for x > 1.

**Operational modes:**

In practice the two protocols appear to be functionally exclusive by mode:

| Mode | Dominant protocol |
|---|---|
| Normal operation (passive/read-only) | Collect autonomous broadcasts |
| Active service session (writes in progress) | Service 77 device-initiated pushes |

Both distribute the same underlying data-point values. Service 77 device pushes
are addressed to specific client channels (with ISO-TP ACK); Collect broadcasts
are unaddressed and require no flow control. A receiver handling both protocols
on the same CAN-ID will typically observe one or the other depending on whether
a write session is active on the bus.

---

### Service 77 opcode summary

All Service 77 frames start with SID `0x77`. The byte or bytes immediately
following the session counter (bytes 3–5 of the reassembled payload) identify
the frame type:

| Bytes 3–5 | Total payload | Direction | Meaning |
|---|---|---|---|
| `43 01 82` | ≥ 10 bytes | Client → Device | **Write request** (data follows) |
| `0x44` (byte 3 only) | 4 bytes | Device → Client | **Write confirmation** (echoes CTR) |
| `43 01 82`, CTR = `0x0000` | ≥ 10 bytes | Device → Client | **Push / sync** (device-initiated) |
| `0x21` (byte 3 only) | 4 bytes | Client → Device | **Session keepalive** request |
| `0x22` (byte 3 only) | 4 bytes | Device → Client | **Session keepalive** response |
| `41 01 82` | 8 bytes | Client → Device | **Read request** (DID only, no data) |
| `42 01 82` | ≥ 10 bytes | Device → Client | **Read response** (echoes CTR + DID, data follows) |

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

---

# External CAN bus — observed CAN-IDs

The external CAN bus connects the Vitocal 250 indoor unit to the Vitocharge VX3
and the E380 energy meter. The table below summarises all CAN-IDs observed in a
one-minute passive capture; it serves as a reference for tools that need to
filter or ignore non-Viessmann traffic.

| CAN-ID(s) | Protocol | Meaning |
|---|---|---|
| `0x441` ↔ `0x451` | Service 77 | S77 request/response for Vitocharge VX3 (`tx = 0x43F`); also carries Collect broadcasts from VX3 on `0x451` |
| `0x250`–`0x25D` | E380 CA | Energy meter broadcasts (see E380 section above) |
| `0x761`, `0x747`, `0x701` | CANopen Heartbeat | Node 97 (E380 CA), Node 71 (VX3), Node 1 |
| `0x271` | CANopen NMT/PDO | Node 0x71 (VX3) |
| `0x647` ↔ `0x5C7` | CANopen SDO | Client/Server, Node 71 (VX3) |
| `0x661` ↔ `0x5E1` | CANopen SDO | Client/Server, Node 97 (E380) |
| `0x6A1` ↔ `0x6B1` | UDS ReadDataByIdentifier | Periodic read of DID `0x2707` approximately every 15 s |
| `0x541` ↔ `0x531` | Proprietary (SDO-like) | Unknown device; exact protocol not identified |
| `0x1FF`, `0x190` | Periodic counter | Incrementing timestamp/counter frames |

**Notes:**

- Only `0x441`/`0x451` carries Service 77 traffic on the external bus. No
  additional S77 pairs were found.
- S77-READ transactions (Client-ID `41 01 82`) have been observed on `0x441`
  reading DID `0x0509` (181 bytes, `0xC1` escape) approximately every 5 s.
- CANopen node IDs follow the standard formula: heartbeat CAN-ID = `0x700 +
  node`, SDO client = `0x600 + node`, SDO server = `0x580 + node`.
