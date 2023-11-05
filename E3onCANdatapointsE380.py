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

dataIdentifiersE380 = {
    0x250: E3ComplexType(8, "GridActivePower", [E3Int16(2, "L1", scale=1.0, signed=True), E3Int16(2, "L2", scale=1.0, signed=True), E3Int16(2, "L3", scale=1.0, signed=True), E3Int16(2, "Total", scale=1.0, signed=True)]),
    0x252: E3ComplexType(8, "GridReactivePower", [E3Int16(2, "L1", scale=1.0, signed=True), E3Int16(2, "L2", scale=1.0, signed=True), E3Int16(2, "L3", scale=1.0, signed=True), E3Int16(2, "Total", scale=1.0, signed=True)]),
    0x254: E3ComplexType(8, "GridCurrent", [E3Int16(2, "L1", scale=1.0, signed=True), E3Int16(2, "L2", scale=1.0, signed=True), E3Int16(2, "L3", scale=1.0, signed=True), E3cosPhi(2, "cosPhi", scale=100.0, signed=True)]),
    0x256: E3ComplexType(8, "GridVoltage", [E3Int16(2, "L1", scale=1.0, signed=False), E3Int16(2, "L2", scale=1.0, signed=False), E3Int16(2, "L3", scale=1.0, signed=False), E3Int16(2, "Frequency", scale=100.0, signed=False)]),
    0x258: E3ComplexType(8, "GridEnergy", [E3Int32(4, "ImportCumulated", scale=1.0, signed=False), E3Int32(4, "ExportCumulated", scale=1.0, signed=False)]),
    0x25A: E3ComplexType(8, "GridPower", [E3Int32(4, "ActivePower", scale=10.0, signed=True), E3Int32(4, "ReactivePower", scale=10.0, signed=True)]),
}
