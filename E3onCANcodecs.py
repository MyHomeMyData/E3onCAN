"""
   Copyright 2023 MyHomeMyData
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from typing import Optional, Any

def getPattern(Id, D0, did) -> str:
    p = ''
    p = p + ''.join('{:04x}'.format(Id))
    p = p + ''.join('{:02x}'.format(D0))
    d = did.to_bytes(2,"big")
    p = p + ''.join('{:02x}'.format(d[1]))
    p = p + ''.join('{:02x}'.format(d[0]))
    return p

class RawCodec():
    def __init__(self, did: int, data_len: int, idStr: str, offset: int = 0, canId: int = 0, canD0: int = 0):
        self.did = did
        self.data_len = data_len
        self.idStr = idStr
        self.offset = offset
        self.canId = canId
        self.canD0 = canD0

    def decode(self, data: bytearray) -> bytearray:
        return data[self.offset:self.offset+self.data_len]

    def pattern(self) -> str:
        return getPattern(self.canId, self.canD0, self.did)

    def __len__(self) -> int:
        return self.data_len

class E3Int16():
    def __init__(self, did:int, data_len: int, idStr: str, signed: bool = True, offset: int = 0, scale: float = 1.0, unit: str = "", canId: int = 0, canD0: int = 0 ):
        self.did = did
        self.data_len = data_len
        self.idStr = idStr
        self.signed = signed
        self.offset = offset
        self.scale = scale
        self.unit = unit
        self.canId = canId
        self.canD0 = canD0

    def decode(self, data: bytearray) -> Any:
        val = int.from_bytes([data[self.offset + 1],data[self.offset + 0]], byteorder="big", signed=self.signed)
        return val / self.scale;

    def pattern(self) -> str:
        return getPattern(self.canId, self.canD0, self.did)

    def __len__(self) -> int:
        return self.data_len
