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

dataIdentifiersE3100CB = {
    "1385.1": E3ComplexType(4, "GridEnergy", [E3Float32(4, "ImportCumulated", scale=1000.0)]),
    "1385.2": E3ComplexType(4, "GridEnergy", [E3Float32(4, "ExportCumulated", scale=1000.0)]),
    "1385.3": E3ComplexType(1, "GridState", [E3StateEM(1, "OperationState", offset=0)]),
    "1385.4": E3ComplexType(4, "GridActivePower", [E3Int16(2, "Total", scale=1.0, signed=True)]),
    "1385.5": E3ComplexType(4, "Unkown_1385_05", [E3Float16(2, "Unknown_0", scale=1.0), E3Float16(2, "Unknown_1", scale=1.0)]),
    "1385.6": E3ComplexType(2, "GridCurrent", [E3Int16(2, "L1", scale=1.0, signed=True)]),
    "1385.7": E3ComplexType(4, "GridVoltage", [E3Int32(4, "L1", scale=1.0, signed=False)]),
    "1385.8": E3ComplexType(4, "GridActivePower", [E3Int16(2, "L1", scale=1.0, signed=True)]),
    "1385.9": E3ComplexType(4, "GridReactivePower", [E3Int16(2, "L1", scale=1.0, signed=True)]),
    "1385.10": E3ComplexType(2, "GridCurrent", [E3Int16(2, "L2", scale=1.0, signed=True)]),
    "1385.11": E3ComplexType(4, "GridVoltage", [E3Int32(4, "L2", scale=1.0, signed=False)]),
    "1385.12": E3ComplexType(4, "GridActivePower", [E3Int16(2, "L2", scale=1.0, signed=True)]),
    "1385.13": E3ComplexType(4, "GridReactivePower", [E3Int16(2, "L2", scale=1.0, signed=True)]),
    "1385.14": E3ComplexType(2, "GridCurrent", [E3Int16(2, "L3", scale=1.0, signed=True)]),
    "1385.15": E3ComplexType(4, "GridVoltage", [E3Int32(4, "L3", scale=1.0, signed=False)]),
    "1385.16": E3ComplexType(4, "GridActivePower", [E3Int16(2, "L3", scale=1.0, signed=True)]),
    "1385.17": E3ComplexType(4, "GridReactivePower", [E3Int16(2, "L3", scale=1.0, signed=True)])
}
