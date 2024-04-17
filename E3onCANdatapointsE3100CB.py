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
    "1385.1": O3EComplexType(4, "GridEnergy", [O3EFloat32(4, "ImportCumulated", scale=1000.0)]),
    "1385.2": O3EComplexType(4, "GridEnergy", [O3EFloat32(4, "ExportCumulated", scale=1000.0)]),
    "1385.3": O3EComplexType(1, "GridState", [O3EStateEM(1, "OperationState", offset=0)]),
    "1385.4": O3EComplexType(4, "GridActivePower", [O3EInt16(2, "Total", scale=1.0, signed=True)]),
    "1385.5": O3EComplexType(4, "Unkown_1385_05", [O3EFloat16(2, "Unknown_0", scale=1.0), O3EFloat16(2, "Unknown_1", scale=1.0)]),
    "1385.6": O3EComplexType(2, "GridCurrent", [O3EInt16(2, "L1", scale=1.0, signed=True)]),
    "1385.7": O3EComplexType(4, "GridVoltage", [O3EInt32(4, "L1", scale=1.0, signed=False)]),
    "1385.8": O3EComplexType(4, "GridActivePower", [O3EInt16(2, "L1", scale=1.0, signed=True)]),
    "1385.9": O3EComplexType(4, "GridReactivePower", [O3EInt16(2, "L1", scale=1.0, signed=True)]),
    "1385.10": O3EComplexType(2, "GridCurrent", [O3EInt16(2, "L2", scale=1.0, signed=True)]),
    "1385.11": O3EComplexType(4, "GridVoltage", [O3EInt32(4, "L2", scale=1.0, signed=False)]),
    "1385.12": O3EComplexType(4, "GridActivePower", [O3EInt16(2, "L2", scale=1.0, signed=True)]),
    "1385.13": O3EComplexType(4, "GridReactivePower", [O3EInt16(2, "L2", scale=1.0, signed=True)]),
    "1385.14": O3EComplexType(2, "GridCurrent", [O3EInt16(2, "L3", scale=1.0, signed=True)]),
    "1385.15": O3EComplexType(4, "GridVoltage", [O3EInt32(4, "L3", scale=1.0, signed=False)]),
    "1385.16": O3EComplexType(4, "GridActivePower", [O3EInt16(2, "L3", scale=1.0, signed=True)]),
    "1385.17": O3EComplexType(4, "GridReactivePower", [O3EInt16(2, "L3", scale=1.0, signed=True)])
}
