"""
   Copyright 2023 MyHomeMyData
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
"),
       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import E3onCANcodecs
from E3onCANcodecs import *

dataIdentifiers = {
     378 : E3Int16( 378, 2, "PointOfCommonCouplingPhaseOne", signed=True, offset=4, scale=1.0, unit="W", canId=0x451, canD0=0x21),
     379 : E3Int16( 379, 2, "PointOfCommonCouplingPhaseOne", signed=True, offset=4, scale=1.0, unit="W", canId=0x451, canD0=0x21),
     380 : E3Int16( 380, 2, "PointOfCommonCouplingPhaseOne", signed=True, offset=4, scale=1.0, unit="W", canId=0x451, canD0=0x21),
    1603 : E3Int16(1603, 2, "PointOfCommonCouplingPower", signed=True, offset=4, scale=1.0, unit="W", canId=0x451, canD0=0x21),
    1690 : E3Int16(1690, 2, "ElectricalEnergySystemPhotovoltaicStatus", signed=True, offset=5, scale=1.0, unit="W", canId=0x451, canD0=0x21),
    1834 : E3Int16(1834, 2, "ElectricalEnergyStorageStateOfEnergy", signed=False, offset=4, scale=1.0, unit="Wh", canId=0x451, canD0=0x21),
    1836 : E3Int16(1836, 2, "ElectricalEnergyStorageCurrentPower", signed=True, offset=4, scale=1.0, unit="W", canId=0x451, canD0=0x21)
}
