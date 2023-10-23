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

dataIdentifiersEM380 = {
   0x250 : E3ComplexType(0x250, 8, "EM380ActivePower", 0, [E3EM380Int(0x250, 2, "L1", scale=1.0, signed=True, unit="W", canId=0x250),
                                                           E3EM380Int(0x250, 2, "L2", scale=1.0, signed=True, unit="W", canId=0x250),
                                                           E3EM380Int(0x250, 2, "L3", scale=1.0, signed=True, unit="W", canId=0x250),
                                                           E3EM380Int(0x250, 2, "Total", scale=1.0, signed=True, unit="W", canId=0x250)],
                                                          canId=0x250),

   0x252 : E3ComplexType(0x252, 8, "EM380ReactivePower", 0, [E3EM380Int(0x252, 2, "L1", scale=1.0, signed=True, unit="W", canId=0x252),
                                                             E3EM380Int(0x252, 2, "L2", scale=1.0, signed=True, unit="W", canId=0x252),
                                                             E3EM380Int(0x252, 2, "L3", scale=1.0, signed=True, unit="W", canId=0x252),
                                                             E3EM380Int(0x252, 2, "Total", scale=1.0, signed=True, unit="W", canId=0x252)],
                                                            canId=0x252),

   0x254 : E3ComplexType(0x254, 2, "EM380cosPhi", 6, [E3EM380cosPhi(0x254, 2, "cosPhi", scale=100.0, signed=True, unit="", canId=0x254)], canId=0x254),

   0x256 : E3ComplexType(0x256, 8, "EM380Voltage", 0, [E3EM380Int(0x256, 2, "L1", scale=1.0, signed=False, unit="V", canId=0x256),
                                                       E3EM380Int(0x256, 2, "L2", scale=1.0, signed=False, unit="V", canId=0x256),
                                                       E3EM380Int(0x256, 2, "L3", scale=1.0, signed=False, unit="V", canId=0x256),
                                                       E3EM380Int(0x256, 2, "Frequency", scale=100.0, signed=False, unit="Hz", canId=0x256)],
                                                      canId=0x256),

   0x25A : E3ComplexType(0x258, 8, "EM380Power", 0, [E3EM380Int(0x25A, 4, "ActivePower", scale=10.0, signed=True, unit="W", canId=0x25A),
                                                     E3EM380Int(0x25A, 4, "ReactivePower", scale=10.0, signed=True, unit="W", canId=0x25A)],
                                                    canId=0x25A)
}
