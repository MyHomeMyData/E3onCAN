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

import can          # https://pypi.org/project/python-can/
import argparse
import time
import paho.mqtt.client as paho

import E3onCANdatapoints
from E3onCANdatapoints import *

import E3onCANcodecs
from E3onCANcodecs import *

def setupCanDict(dids, dataIDs):
    CanDict = {}
    filters = []
    canIDs  = []
    for did in dids:
        dataID = dataIDs[eval(did)]
        CanDict[dataID.pattern()] = dataID
        if not (dataID.canId in canIDs):
            filters.append({"can_id": dataID.canId, "can_mask": 0x7FF, "extended": False})
            canIDs.append(dataID.canId)
    return CanDict, filters

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--can", type=str, help="use can device, e.g. can0")
parser.add_argument("-r", "--read", type=str, help="read did, e.g. 0x173,0x174")
parser.add_argument("-m", "--mqtt", type=str, help="publish to server, e.g. 192.168.0.1:1883:topicname")
parser.add_argument("-mfstr", "--mqttformatstring", type=str, help="mqtt formatstring e.g. {didNumber}_{didName}")
parser.add_argument("-muser", "--mqttuser", type=str, help="mqtt username")
parser.add_argument("-mpass", "--mqttpass", type=str, help="mqtt password")
parser.add_argument("-v", "--verbose", action='store_true', help="verbose info")
args = parser.parse_args()

if (args.read != None):
    CanDict, filters = setupCanDict(args.read.split(","), dataIdentifiers)
else:
    print('No did(s) specified. "E3onCAN -h" for help.')
    exit(0)

if(args.can != None):
    channel = args.can
else:
    channel = 'can0'

client_mqtt = None
mqttParamas = None
mqttformatstring = "{didName}"
if(args.mqtt != None):
    mqttParamas = args.mqtt.split(":")
    if(args.mqttformatstring != None):
        mqttformatstring = args.mqttformatstring
    client_mqtt = paho.Client("E3onCANclient.py")
    if((args.mqttuser != None) and (args.mqttpass != None)):
        client_mqtt.username_pw_set(args.mqttuser , password=args.mqttpass)
    client_mqtt.connect(mqttParamas[0], int(mqttParamas[1]))
    client_mqtt.reconnect_delay_set(min_delay=1, max_delay=30)
    client_mqtt.loop_start()
    print("Wait for dids and publish to mqtt...")
    
try:
    with can.Bus(interface='socketcan',
                  channel=channel,
                  receive_own_messages=True, can_filters=filters) as bus:

        # iterate over received messages
        for msg in bus:
            did = msg.data[1]+256*msg.data[2]
            p = getPattern(msg.arbitration_id,msg.data[0],did)
            if p in CanDict:
                dataID = CanDict[p]
                valStr = str(dataID.decode(msg.data))
                if (args.mqtt != None):
                    topicStr = mqttformatstring.format(
                        didName = dataID.idStr,
                        didNumber = did
                    )
                    ret = client_mqtt.publish(mqttParamas[2] + "/" + topicStr, valStr)
                if (args.verbose == True):
                    print (str(did), dataID.idStr, valStr)

except (KeyboardInterrupt, InterruptedError):
    # got <STRG-C> or SIGINT (<kill -s SIGINT pid>)
    pass
