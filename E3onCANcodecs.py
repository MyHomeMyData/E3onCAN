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
from udsoncan.common.DidCodec import DidCodec
from typing import Optional, Any
import struct

flag_rawmode = True

class E3RawCodec(DidCodec):
    def __init__(self, string_len: int, idStr: str):
        self.string_len = string_len
        self.id = idStr
        self.complex = False

    def decode(self, string_bin: bytes) -> Any:
        string_ascii = string_bin.hex()
        return string_ascii

    def __len__(self) -> int:
        return self.string_len

class E3Float16(DidCodec):
    def __init__(self, string_len: int, idStr: str, scale: float = 1.0, offset: int = 0):
        self.string_len = string_len
        self.id = idStr
        self.complex = False
        self.scale = scale
        self.offset = offset

    def decode(self, string_bin: bytes) -> Any:
        if(flag_rawmode == True): 
            return E3RawCodec.decode(self, string_bin)
        val = struct.unpack('e', string_bin[self.offset:self.offset+self.string_len])[0]
        return float(val) / self.scale

    def __len__(self) -> int:
        return self.string_len

class E3Float32(DidCodec):
    def __init__(self, string_len: int, idStr: str, scale: float = 1.0, offset: int = 0):
        self.string_len = string_len
        self.id = idStr
        self.complex = False
        self.scale = scale
        self.offset = offset

    def decode(self, string_bin: bytes) -> Any:
        if(flag_rawmode == True): 
            return E3RawCodec.decode(self, string_bin)
        val = struct.unpack('f', string_bin[self.offset:self.offset+self.string_len])[0]
        return float(val) / self.scale

    def __len__(self) -> int:
        return self.string_len

class E3Float64(DidCodec):
    def __init__(self, string_len: int, idStr: str, scale: float = 1.0, offset: int = 0):
        self.string_len = string_len
        self.id = idStr
        self.complex = False
        self.scale = scale
        self.offset = offset

    def decode(self, string_bin: bytes) -> Any:
        if(flag_rawmode == True): 
            return E3RawCodec.decode(self, string_bin)
        val = struct.unpack('d', string_bin[self.offset:self.offset+self.string_len])[0]
        return float(val) / self.scale

    def __len__(self) -> int:
        return self.string_len

class E3Int(DidCodec):
    def __init__(self, string_len: int, idStr: str, byte_width: int, scale: float = 1.0, offset: int = 0, signed=False):
        self.string_len = string_len
        self.byte_width = byte_width
        self.id = idStr
        self.complex = False
        self.scale = scale
        self.offset = offset
        self.signed = signed

    def decode(self, string_bin: bytes) -> Any:
        if(flag_rawmode == True): 
            return E3RawCodec.decode(self, string_bin)
        val = int.from_bytes(string_bin[self.offset:self.offset + self.byte_width], byteorder="little", signed=self.signed)
        return float(val) / self.scale

    def __len__(self) -> int:
        return self.string_len

class E3Int8(E3Int):
    def __init__(self, string_len: int, idStr: str, scale: float = 1.0, offset: int = 0, signed=False):
        E3Int.__init__(self, string_len, idStr, byte_width=1, scale=scale, offset=offset, signed=signed)

class E3Int16(E3Int):
    def __init__(self, string_len: int, idStr: str, scale: float = 10.0, offset: int = 0, signed=False):
        E3Int.__init__(self, string_len, idStr, byte_width=2, scale=scale, offset=offset, signed=signed)

class E3Int32(E3Int):
    def __init__(self, string_len: int, idStr: str, scale: float = 1.0, offset: int = 0, signed=False):
        E3Int.__init__(self, string_len, idStr, byte_width=4, scale=scale, offset=offset, signed=signed)

class E3cosPhi():
    def __init__(self, string_len: int, idStr: str, scale: float = 1.0, signed: bool = True, offset: int = 0):
        self.string_len = string_len
        self.id = idStr
        self.scale = scale
        self.signed = signed
        self.offset = offset
        self.complex = False

    def decode(self, string_bin: bytes) -> Any:
        if (flag_rawmode == True): 
            return E3RawCodec.decode(self, string_bin)
        val = string_bin[1+self.offset]
        if string_bin[self.offset] == 0x04:
            val = -1.0*val
        return val/self.scale

    def __len__(self) -> int:
        return self.string_len

class E3ComplexType():
    def __init__(self, string_len: int, idStr: str, subTypes : list):
        self.string_len = string_len
        self.id = idStr
        self.subTypes = subTypes
        self.complex = True

    def decode(self, string_bin: bytes) -> Any:
        if (flag_rawmode == True): 
            return E3RawCodec.decode(self, string_bin)
        result = dict()
        index = 0
        for subType in self.subTypes:
            result[subType.id] = subType.decode(string_bin[index:index+subType.string_len])
            index+=subType.string_len
        return dict(result)
    
    def __len__(self) -> int:
        return self.string_len

class E3StateEM(DidCodec):
    def __init__(self, string_len: int, idStr: str, offset: int = 0):
        self.string_len = string_len
        self.id = idStr
        self.offset = offset

    def decode(self, string_bin: bytes) -> Any:
        if(flag_rawmode == True): 
            return E3RawCodec.decode(self, string_bin)
        val = string_bin[self.offset]
        if val == 4:
            return -1
        if val == 0:
            return 1
        return 0

    def __len__(self) -> int:
        return self.string_len
