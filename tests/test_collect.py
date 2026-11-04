import collections
import json
import random
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# DIDs in this range are unknown to the data point lists
DID_A, DID_B, DID_C = 9001, 9002, 9003

CIRCUIT_NAME_OG = "45472f4f470000000000000000000000000000000000000000000000000000000000000000000000"
CIRCUIT_NAME_UG = "55470000ffffffff00000000010000005a360203a300007a495a360003a500007a495a3600000000"


def single_frame(did, payload):
    return [[0x21, did & 0xFF, did >> 8, 0xB0 + len(payload), *payload]]


def multi_frame(did, payload, kind="c1"):
    n = len(payload)
    if kind == "c1":
        first, rest = [0x21, did & 0xFF, did >> 8, 0xB0, 0xC1, n, *payload[:2]], payload[2:]
    elif kind == "b0":
        first, rest = [0x21, did & 0xFF, did >> 8, 0xB0, n, *payload[:3]], payload[3:]
    else:
        first, rest = [0x21, did & 0xFF, did >> 8, 0xB0 + n, *payload[:4]], payload[4:]
    frames = [first]
    seq = 0x22
    while rest:
        frames.append([seq, *rest[:7]])
        rest = rest[7:]
        seq = 0x20 if seq == 0x2F else seq + 1
    return frames


def dump_line(can_id, frame):
    data = " ".join(f"{b:02X}" for b in frame + [0] * (8 - len(frame)))
    return f"  can0  {can_id:03X}   [8]  {data}"


def dump(*frames_with_id):
    return [dump_line(can_id, frame) for can_id, frames in frames_with_id for frame in frames]


def run_collect(tmp_path, lines, *args):
    fn = tmp_path / "candump.txt"
    fn.write_text("\n".join(lines) + "\n")
    return subprocess.run(
        [sys.executable, str(REPO / "E3onCANcollect.py"), "-f", str(fn), "-v", *args],
        capture_output=True, text=True, cwd=REPO, timeout=60,
    )


def parse(stdout):
    """Return list of (did, name, value) for all lines holding a decoded did."""
    result = []
    for line in stdout.splitlines():
        match = re.match(r"(?:\d{4}-\d\d-\d\d \S+ )?(\d+(?:\.\d+)?) (\S+): (.*)$", line)
        if match:
            result.append((match[1], match[2], json.loads(match[3])))
    return result


def raw_values(stdout):
    """Return list of (did, hex string) of output created with option -raw."""
    return [(int(did), value["Raw"] if isinstance(value, dict) else value) for did, _, value in parse(stdout)]


def run_raw(tmp_path, lines, *args):
    proc = run_collect(tmp_path, lines, "-raw", *args)
    assert proc.returncode == 0, proc.stderr
    return proc, raw_values(proc.stdout)


PAYLOAD_A = list(range(0x11, 0x19))
PAYLOAD_B = list(range(0xA1, 0xA9))
TWO_IDS = dump((0x441, multi_frame(DID_A, PAYLOAD_A)), (0x451, multi_frame(DID_B, PAYLOAD_B)), (0x693, single_frame(DID_C, [0xC1])))


# --- option --canid ---

@pytest.mark.parametrize("canid, expected", [
    ("0x441", [DID_A]),
    ("0x451", [DID_B]),
    ("0x441,0x451", [DID_A, DID_B]),
    ("0x441,0x451,0x693", [DID_A, DID_B, DID_C]),
    ("1105,0x693", [DID_B, DID_C]),
    ("0x441,0x441", [DID_A]),
])
def test_canid_selects_can_ids(tmp_path, canid, expected):
    proc, values = run_raw(tmp_path, TWO_IDS, "-dev", "vx3", "-canid", canid)
    assert [did for did, _ in values] == expected
    assert "WARNING" not in proc.stdout


@pytest.mark.parametrize("canid", ["0x441, 0x451", "0x441 ,0x451", " 0x441", "0x441,", ",0x441", "0x441,abc", "abc", ""])
def test_invalid_canid_falls_back_to_device_default(tmp_path, canid):
    proc, values = run_raw(tmp_path, TWO_IDS, "-dev", "vx3", "-canid", canid)
    assert "WARNING: Could not evaluate given canid" in proc.stdout
    assert [did for did, _ in values] == [DID_A, DID_B]


@pytest.mark.parametrize("device, expected", [
    ("vx3", [DID_A, DID_B]),
    ("vair", [DID_B]),
    ("vdens", [DID_B]),
    ("vcal", [DID_C]),
])
def test_device_selects_default_can_ids(tmp_path, device, expected):
    _, values = run_raw(tmp_path, TWO_IDS, "-dev", device)
    assert [did for did, _ in values] == expected


@pytest.mark.parametrize("device", ["e380", "e3100cb"])
def test_canid_not_allowed_for_energy_meter(tmp_path, device):
    proc = run_collect(tmp_path, TWO_IDS, "-dev", device, "-canid", "0x441,0x451")
    assert "not allowed for energy meter" in proc.stdout
    assert parse(proc.stdout) == []


# --- collecting of frames ---

def test_interleaved_multi_frames_of_different_can_ids(tmp_path):
    a = multi_frame(DID_A, PAYLOAD_A)
    b = multi_frame(DID_B, PAYLOAD_B)
    lines = [dump_line(0x451, a[0]), dump_line(0x441, b[0]), dump_line(0x451, a[1]), dump_line(0x441, b[1])]
    _, values = run_raw(tmp_path, lines, "-dev", "vx3")
    assert values == [(DID_A, bytes(PAYLOAD_A).hex()), (DID_B, bytes(PAYLOAD_B).hex())]


@pytest.mark.parametrize("kind, length", [("b5", 5), ("b5", 15), ("b0", 3), ("b0", 4), ("b0", 100), ("c1", 2), ("c1", 40), ("c1", 180)])
def test_multi_frame_is_decoded_without_following_frame(tmp_path, kind, length):
    payload = [i & 0xFF for i in range(length)]
    _, values = run_raw(tmp_path, dump((0x451, multi_frame(DID_A, payload, kind))), "-dev", "vx3")
    assert values == [(DID_A, bytes(payload).hex())]


def test_telegram_following_sequence_counter_wrap_is_kept(tmp_path):
    # 16 frames of DID_A: next expected sequence byte is 0x21, same as first byte of next telegram
    payload = [i & 0xFF for i in range(107)]
    frames = multi_frame(DID_A, payload)
    assert len(frames) == 16
    lines = dump((0x451, frames), (0x451, single_frame(DID_B, [0xAA, 0xBB])), (0x451, single_frame(DID_C, [0xCC])))
    _, values = run_raw(tmp_path, lines, "-dev", "vx3")
    assert values == [(DID_A, bytes(payload).hex()), (DID_B, "aabb"), (DID_C, "cc")]


def test_incomplete_multi_frame_is_dropped(tmp_path):
    frames = multi_frame(DID_A, PAYLOAD_A + PAYLOAD_B)[:-1]
    lines = dump((0x451, frames), (0x451, single_frame(DID_B, [0xAA])))
    _, values = run_raw(tmp_path, lines, "-dev", "vx3")
    assert values == [(DID_B, "aa")]


@pytest.mark.parametrize("ids", [[0x451], [0x441, 0x451]])
@pytest.mark.parametrize("seed", range(3))
def test_random_telegrams(tmp_path, seed, ids):
    rng = random.Random(seed)
    queues = {can_id: [] for can_id in ids}
    expected = collections.Counter()
    for did in range(9000, 9200):
        kind = rng.choice(["single", "b5", "b0", "c1"])
        length = {"single": rng.randint(1, 4), "b5": rng.randint(5, 15), "b0": rng.randint(1, 180), "c1": rng.randint(1, 180)}[kind]
        if kind == "b0" and length == 0xC1:
            length = 100
        payload = [rng.randint(0, 255) for _ in range(length)]
        frames = single_frame(did, payload) if kind == "single" else multi_frame(did, payload, kind)
        # lost last frame: short telegrams only, otherwise next start frame may match sequence after wrap
        if 1 < len(frames) < 14 and rng.random() < 0.1:
            frames = frames[:-1]
        else:
            expected[(did, bytes(payload).hex())] += 1
        queues[rng.choice(ids)].append(frames)

    lines = []
    current = {can_id: [] for can_id in ids}
    while any(queues[can_id] or current[can_id] for can_id in ids):
        can_id = rng.choice([i for i in ids if queues[i] or current[i]])
        if not current[can_id]:
            current[can_id] = list(queues[can_id].pop(0))
        lines.append(dump_line(can_id, current[can_id].pop(0)))

    _, values = run_raw(tmp_path, lines, "-dev", "vx3")
    assert collections.Counter(values) == expected


# --- decoding, option -r and -g ---

@pytest.mark.parametrize("did, name, raw, expected", [
    (627, "CentralHeatingOneCircuitName", CIRCUIT_NAME_OG, "EG/OG"),
    (628, "CentralHeatingTwoCircuitName", CIRCUIT_NAME_UG, "UG"),
])
def test_circuit_names_end_at_first_nul(tmp_path, did, name, raw, expected):
    lines = dump((0x451, multi_frame(did, list(bytes.fromhex(raw)))))
    proc = run_collect(tmp_path, lines, "-dev", "vx3")
    assert parse(proc.stdout) == [(str(did), name, expected)]


def test_read_filters_dids(tmp_path):
    lines = dump((0x451, single_frame(DID_A, [1])), (0x451, multi_frame(DID_B, PAYLOAD_B)), (0x451, single_frame(DID_C, [3])))
    _, values = run_raw(tmp_path, lines, "-dev", "vx3", "-r", f"{DID_B},{hex(DID_C)}")
    assert [did for did, _ in values] == [DID_B, DID_C]


def test_read_filter_drops_multi_frame(tmp_path):
    lines = dump((0x451, multi_frame(DID_A, PAYLOAD_A)), (0x451, single_frame(DID_B, [2])))
    _, values = run_raw(tmp_path, lines, "-dev", "vx3", "-r", str(DID_B))
    assert values == [(DID_B, "02")]


def test_gap_suppresses_repeated_did(tmp_path):
    lines = dump((0x451, single_frame(DID_A, [1])), (0x451, single_frame(DID_B, [2])), (0x451, single_frame(DID_A, [3])))
    _, values = run_raw(tmp_path, lines, "-dev", "vx3", "-g", "3600")
    assert values == [(DID_A, "01"), (DID_B, "02")]


def test_unknown_did_is_reported(tmp_path):
    proc = run_collect(tmp_path, dump((0x451, single_frame(DID_A, [0x12, 0x34]))), "-dev", "vx3")
    assert parse(proc.stdout) == [(str(DID_A), "Unknown", {"Error": "No codec found for did", "Did": DID_A, "Raw": "1234"})]


def test_unknown_device_is_rejected(tmp_path):
    proc = run_collect(tmp_path, TWO_IDS, "-dev", "foo")
    assert "Unknown device foo" in proc.stdout
    assert parse(proc.stdout) == []


# --- energy meters ---

def test_e380_uses_can_id_as_did(tmp_path):
    values = struct.pack("<4h", 96, 7, -108, -5)
    lines = [dump_line(0x250, list(values)), dump_line(0x251, list(values)), dump_line(0x451, list(values))]
    proc = run_collect(tmp_path, lines, "-dev", "e380")
    power = {"L1": 96.0, "L2": 7.0, "L3": -108.0, "Total": -5.0}
    assert parse(proc.stdout) == [(str(0x250), "GridActivePower", power), (str(0x251), "GridActivePower", power)]


def test_e380_read_filters_can_ids(tmp_path):
    frame = list(struct.pack("<4h", 1, 2, 3, 4))
    lines = [dump_line(0x250, frame), dump_line(0x252, frame), dump_line(0x254, frame)]
    proc = run_collect(tmp_path, lines, "-dev", "e380", "-r", "0x252")
    assert [did for did, _, _ in parse(proc.stdout)] == [str(0x252)]


def test_e3100cb_uses_can_id_and_data_byte_3_as_did(tmp_path):
    frame = [0, 0, 0, 1, *struct.pack("<f", 1000.0)]
    proc = run_collect(tmp_path, [dump_line(0x569, frame), dump_line(0x451, frame)], "-dev", "e3100cb")
    assert parse(proc.stdout) == [("1385.01", "GridEnergy", {"ImportCumulated": 1.0})]


def test_e3100cb_read_filters_dids(tmp_path):
    lines = [dump_line(0x569, [0, 0, 0, sub, 0, 0, 0, 0]) for sub in (1, 2, 4)]
    proc = run_collect(tmp_path, lines, "-dev", "e3100cb", "-r", "1385.02")
    assert [did for did, _, _ in parse(proc.stdout)] == ["1385.02"]


# --- candump formats ---

@pytest.mark.parametrize("template", [
    "  can0  451   [8]  {spaced}",
    " (1697695707.985038)  can0  451   [8]  {spaced}",
    " (2023-03-12 10:03:51.202750)  can0  451   [8]  {spaced}",
    "(1678484087.154260) can0 451#{joined}",
], ids=["simple", "ts long", "datetime", "ts short"])
def test_candump_formats(tmp_path, template):
    lines = []
    for frame in multi_frame(DID_A, PAYLOAD_A):
        frame = frame + [0] * (8 - len(frame))
        lines.append(template.format(spaced=" ".join(f"{b:02X}" for b in frame), joined="".join(f"{b:02X}" for b in frame)))
    _, values = run_raw(tmp_path, lines, "-dev", "vx3")
    assert values == [(DID_A, bytes(PAYLOAD_A).hex())]


def test_unknown_candump_format_is_rejected(tmp_path):
    proc = run_collect(tmp_path, ["no valid candump line"], "-dev", "vx3")
    assert "File format not recognized" in proc.stdout
