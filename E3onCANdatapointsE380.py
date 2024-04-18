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
    # Even ID => E380 with CAN-address=97
    # Odd ID  => E380 with CAN-address=98
    0x250: O3EComplexType(8, "GridActivePower", [O3EInt16(2, "L1", scale=1.0, signed=True), O3EInt16(2, "L2", scale=1.0, signed=True), O3EInt16(2, "L3", scale=1.0, signed=True), O3EInt16(2, "Total", scale=1.0, signed=True)]),
    0x251: O3EComplexType(8, "GridActivePower", [O3EInt16(2, "L1", scale=1.0, signed=True), O3EInt16(2, "L2", scale=1.0, signed=True), O3EInt16(2, "L3", scale=1.0, signed=True), O3EInt16(2, "Total", scale=1.0, signed=True)]),
    0x252: O3EComplexType(8, "GridReactivePower", [O3EInt16(2, "L1", scale=1.0, signed=True), O3EInt16(2, "L2", scale=1.0, signed=True), O3EInt16(2, "L3", scale=1.0, signed=True), O3EInt16(2, "Total", scale=1.0, signed=True)]),
    0x253: O3EComplexType(8, "GridReactivePower", [O3EInt16(2, "L1", scale=1.0, signed=True), O3EInt16(2, "L2", scale=1.0, signed=True), O3EInt16(2, "L3", scale=1.0, signed=True), O3EInt16(2, "Total", scale=1.0, signed=True)]),
    0x254: O3EComplexType(8, "GridCurrent", [O3EInt16(2, "Absolute L1", scale=1.0, signed=True), O3EInt16(2, "Absolute L2", scale=1.0, signed=True), O3EInt16(2, "Absolute L3", scale=1.0, signed=True), O3EcosPhi(2, "cosPhi", scale=100.0, signed=True)]),
    0x255: O3EComplexType(8, "GridCurrent", [O3EInt16(2, "Absolute L1", scale=1.0, signed=True), O3EInt16(2, "Absolute L2", scale=1.0, signed=True), O3EInt16(2, "Absolute L3", scale=1.0, signed=True), O3EcosPhi(2, "cosPhi", scale=100.0, signed=True)]),
    0x256: O3EComplexType(8, "GridVoltage", [O3EInt16(2, "L1", scale=1.0, signed=False), O3EInt16(2, "L2", scale=1.0, signed=False), O3EInt16(2, "L3", scale=1.0, signed=False), O3EInt16(2, "Frequency", scale=100.0, signed=False)]),
    0x257: O3EComplexType(8, "GridVoltage", [O3EInt16(2, "L1", scale=1.0, signed=False), O3EInt16(2, "L2", scale=1.0, signed=False), O3EInt16(2, "L3", scale=1.0, signed=False), O3EInt16(2, "Frequency", scale=100.0, signed=False)]),
    0x258: O3EComplexType(8, "GridEnergy", [O3EFloat32(4, "ImportCumulated", scale=1000.0), O3EFloat32(4, "ExportCumulated", scale=1000.0)]),  # Cumulated import and export (kWh)
    0x259: O3EComplexType(8, "GridEnergy", [O3EFloat32(4, "ImportCumulated", scale=1000.0), O3EFloat32(4, "ExportCumulated", scale=1000.0)]),  # Cumulated import and export (kWh)
    0x25A: O3EComplexType(8, "GridPower", [O3EInt32(4, "ActivePower", scale=10.0, signed=True), O3EInt32(4, "ReactivePower", scale=10.0, signed=True)]),
    0x25B: O3EComplexType(8, "GridPower", [O3EInt32(4, "ActivePower", scale=10.0, signed=True), O3EInt32(4, "ReactivePower", scale=10.0, signed=True)]),
    0x25C: O3EComplexType(8, "GridEnergy", [O3EInt32(4, "ImportCumulated", scale=100, signed=False), O3EInt32(4, "Unknown", scale=1, signed=False)]),   # Cumulated import (kWh)
    0x25D: O3EComplexType(8, "GridEnergy", [O3EInt32(4, "ImportCumulated", scale=100, signed=False), O3EInt32(4, "Unknown", scale=1, signed=False)])    # Cumulated import (kWh)
}
