import random
import re

import pytest

import E3onCANcodecs
import Open3Ecodecs
from E3onCANdatapointsE380 import dataIdentifiersE380
from E3onCANdatapointsE3100CB import dataIdentifiersE3100CB
from Open3Edatapoints import dataIdentifiers as commonIdentifiers
from Open3EdatapointsVariants import dataIdentifiers as variantIdentifiers

CAN_ID_E3100CB = 0x569
MAX_CAN_ID = 0x7FF

variants = [
    (did, didLen, codec)
    for did, codecs in variantIdentifiers["dids"].items()
    for didLen, codec in codecs.items()
]


@pytest.fixture(autouse=True)
def decoded_mode(monkeypatch):
    monkeypatch.setattr(Open3Ecodecs, "flag_rawmode", False)
    monkeypatch.setattr(E3onCANcodecs, "flag_rawmode", False)


def _calc_codec_length(codec):
    if hasattr(codec, "subTypes"):
        return sum(_calc_codec_length(sub) for sub in codec.subTypes)
    return len(codec)


@pytest.mark.parametrize("did, didLen, codec", variants)
def test_variant_key_matches_codec_length(did, didLen, codec):
    assert len(codec) == didLen, f"Did {did}"


@pytest.mark.parametrize("did, didLen, codec", variants)
def test_variant_length_matches_sum_of_subtypes(did, didLen, codec):
    assert _calc_codec_length(codec) == didLen, f"Did {did}"


@pytest.mark.parametrize("did", variantIdentifiers["dids"])
def test_variant_did_exists_in_common_list(did):
    # getFullDidsList() only merges variants of dids listed in the common list
    assert did in commonIdentifiers["dids"]


@pytest.mark.parametrize("did, codec", dataIdentifiersE380.items())
def test_e380_codec_decodes_can_payload(did, codec):
    assert 0 <= did <= MAX_CAN_ID
    assert _calc_codec_length(codec) <= 8
    assert len(codec) == 8
    assert isinstance(codec.decode(random.randbytes(8)), dict)


@pytest.mark.parametrize("did, codec", dataIdentifiersE3100CB.items())
def test_e3100cb_codec_decodes_can_payload(did, codec):
    # did is built from CAN id and data byte 3, the remaining 4 bytes are decoded
    assert re.fullmatch(rf"{CAN_ID_E3100CB}\.\d\d", did)
    assert _calc_codec_length(codec) <= 4
    assert len(codec) == 4
    assert isinstance(codec.decode(random.randbytes(4)), dict)
