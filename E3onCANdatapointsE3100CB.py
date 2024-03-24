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

import E3onCANcodecs
from E3onCANcodecs import *

dataIdentifiersE100CB = {
    "1385.4": E3ComplexType(8, "E3100_1385.4", [E3Int8(1, "D0", scale=1.0, signed=True), E3Int8(1, "D1", scale=1.0, signed=True), E3Int8(1, "D2", scale=1.0, signed=True), E3Int8(1, "D3", scale=1.0, signed=True), E3Int16(2, "VAL0_16", scale=1.0, signed=True), E3Int16(2, "VAL1_16", scale=1.0, signed=True)])
}
