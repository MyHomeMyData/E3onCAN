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
import paho.mqtt.client as paho
import importlib
import datetime

import Open3Edatapoints
from Open3Edatapoints import *

import E3onCANdatapointsE380
from E3onCANdatapointsE380 import *

import Open3Ecodecs
from Open3Ecodecs import *

import E3onCANcodecs
from E3onCANcodecs import *

def decodeData(device, canid, ts, did, databytes):
    def mqttdump(topic, obj, set_retain):
        if (type(obj)==dict):
            for k, itm in obj.items():
                mqttdump(topic+'/'+str(k),itm, set_retain)
        elif (type(obj)==list):
            for k in range(len(obj)):
                mqttdump(topic+'/'+str(k),obj[k], set_retain)
        else:
            ret = client_mqtt.publish(topic, str(obj), retain=set_retain)                  

    if did in dataIdentifiers:
        try:
            topicPf = ''    # clear topic Prefix
            didNAME = dataIdentifiers[did].id
            values  = dataIdentifiers[did].decode(databytes)
        except Exception as e:
            # Exception while decoding
            topicPf = "$"   # set topic Prefix
            values = {
                        "Error": "Exception: "+str(e),
                        "Did": did,
                        "Raw": databytes.hex()
                     }
    else:
        # No codec available for this did
        topicPf = "$"   # set topic Prefix
        didNAME = "Unknown"
        values = {
                    "Error": "No codec found for did",
                    "Did": did,
                    "Raw": databytes.hex()
                 }

    if (args.mqtt != None):
        topicStr = topicPf + mqttformatstring.format(
            device = device,
            didName = didNAME,
            didNumber = did
        )
        set_retain = (retainall == True) or (did in retaindids)

        if (args.json == True): 
            # Send one JSON message 
            ret = client_mqtt.publish(mqttParamas[2] + "/" + topicStr, json.dumps(values))    
        else:
            # Split down to scalar types
            mqttdump(mqttParamas[2] + "/" + topicStr, values, set_retain)
        if (args.verbose == True):
            print(str(did)+' '+didNAME+': '+json.dumps(values))
    else:
        if (args.verbose == True):
            if ts > 0:
                dt_str = str(datetime.datetime.fromtimestamp(ts))+' '
            else:
                dt_str = ''
            print(dt_str+str(did)+' '+didNAME+': '+json.dumps(values))
        else:
            print(didNAME+': '+json.dumps(values))

def evalMessages(bus, device, args):
    data = {
            "len"       : 0,
            "timestamp" : 0,
            "databytes" : bytearray(),
            "did"       : 0,
            "collecting": False,
            "D0expected": 0x21,
    }

    for msg in bus:
        id = msg.arbitration_id
        if args.dev == 'e380':
            # e380 sends 8 bytes of data w/o any protocol
            # use CAN id as did
            did = id
            decodeData(device,id,msg.timestamp,did,msg.data)
        else:
            if data["collecting"]:
                if msg.data[0] == data["D0expected"]:
                    # append next part of data
                    data["databytes"] += msg.data[1:]
                    data["D0expected"] += 1
                    if data["D0expected"] > 0x2f:
                        data["D0expected"] = 0x20
                else:
                    # no more data
                    if ((dids == None) or (data["did"] in dids)) and (len(data["databytes"]) >= data["len"]):
                        decodeData(device, id, data["timestamp"], data["did"],data["databytes"][0:data["len"]])
                    data["collecting"] = False

            if not data["collecting"] and (msg.dlc > 4) and (msg.data[0] == 0x21) and (msg.data[3] in range(0xb0,0xc0)):
                data["did"] = msg.data[1]+256*msg.data[2]
                if data["did"] > 0 and data["did"] < 10000:
                    data["timestamp"] = msg.timestamp
                    D3 = msg.data[3]
                    if D3 in [0xb1,0xb2,0xb3,0xb4]:
                        # Single Frame B1,B2,B3,B4
                        data["len"] = D3-0xb0
                        data["databytes"] = msg.data[4:]
                        decodeData(device, id, data["timestamp"], data["did"],data["databytes"][0:data["len"]])

                    if D3 == 0xb0:
                        # Multi Frame B0
                        data["D0expected"] = msg.data[0]+1
                        if msg.data[4]==0xc1:
                            data["len"] = msg.data[5]
                            data["databytes"] = msg.data[6:]
                        else:
                            data["len"] = msg.data[4]
                            data["databytes"] = msg.data[5:]

                    if D3 in range(0xb5,0xc0):
                        # Multi Frame B5 .. BF
                        data["D0expected"] = msg.data[0]+1
                        data["len"] = D3-0xb0
                        data["databytes"] = msg.data[4:]

                    data["collecting"] = True

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--can", type=str, help="use can device, e.g. can0")
parser.add_argument("-f", "--file", type=str, help="use candump as input, e.g. candump_vx3")
parser.add_argument("-dev", "--dev", type=str, help="device type --dev vcal or --dev vx3 or --dev vair or --dev vdens or --dev e380")
parser.add_argument("-canid", "--canid", type=str, help="CAN id to listen to --canid  0x451, overrides CAN id selected by device")
parser.add_argument("-r", "--read", type=str, help="read did, e.g. 0x173,0x174")
parser.add_argument("-raw", "--raw", action='store_true', help="return raw data for all dids")
parser.add_argument("-m", "--mqtt", type=str, help="publish to server, e.g. 192.168.0.1:1883:topicname")
parser.add_argument("-mfstr", "--mqttformatstring", type=str, help="mqtt formatstring e.g. {didNumber}_{didName}")
parser.add_argument("-muser", "--mqttuser", type=str, help="mqtt username")
parser.add_argument("-mpass", "--mqttpass", type=str, help="mqtt password")
parser.add_argument("-j", "--json", action='store_true', help="send JSON structure")
parser.add_argument("-retain", "--retain", type=str, help="set retained flag for dids, e.g. 1834,1836")
parser.add_argument("-retainall", "--retainall", action='store_true', help="set retained flag for all dids")
parser.add_argument("-v", "--verbose", action='store_true', help="verbose info")
args = parser.parse_args()

Open3Ecodecs.flag_rawmode = args.raw
E3onCANcodecs.flag_rawmode = args.raw

if(args.dev != None):
    device = args.dev
else:
    device = 'vx3'
    print('No device specified. Using '+device+' as default.')

Open3Ecodecs.flag_dev = device

if not device in ['vx3','vair','vcal','vdens','e380']:
    print('Unknown device '+device+'. Aborting.')
    exit(0)

if (device == 'e380') and (args.canid != None):
    print('Specification CAN ids not allowed for device E380. Aborting.')
    exit(0)

if device == 'e380':
    dataIdentifiers = dataIdentifiersE380
else:
    # load datapoints for selected device
    module_name =  "Open3Edatapoints" + device.capitalize()
    didmoduledev = importlib.import_module(module_name)
    dataIdentifiersDev = didmoduledev.dataIdentifiers["dids"]

    # load general datapoints table from Open3Edatapoints.py
    dataIdentifiers = dataIdentifiers["dids"]

    # overlay device dids over general table 
    lstpops = []
    for itm in dataIdentifiers:
        if not (itm in dataIdentifiersDev):
            lstpops.append(itm)
        elif not (dataIdentifiersDev[itm] is None):  # None means 'no change', nothing special
            dataIdentifiers[itm] = dataIdentifiersDev[itm]

    # remove dids not existing with the device
    for itm in lstpops:
        dataIdentifiers.pop(itm)

    # probably useless but to indicate that it's not required anymore
    dataIdentifiersDev = None
    didmoduledev = None

devCANid = {
    "vcal" : 0x693,
    "vx3"  : 0x451,
    "vair" : 0x451,
    "vdens": 0x451,
    "e380" : list(dataIdentifiersE380.keys())
}

if (args.canid != None):
    CANid = eval(args.canid)
else:
    CANid = devCANid[device]

if (args.read != None):
    dids_str=args.read.split(",")
    dids = []
    for did in dids_str:
        if ((args.dev != 'e380') or ((args.dev == 'e380') and (eval(did) in CANid))):
            dids.append(eval(did))
else:
    dids = None

if (dids == []):
    print('No valid dids specified. Aborting.')
    exit(0)

if args.dev == 'e380':
    filters = []
    for id in CANid:
        if dids == None or id in dids:
            filters.append({"can_id": id, "can_mask": 0x7FF, "extended": False})
else:
    filters = [{"can_id": CANid, "can_mask": 0x7FF, "extended": False}]

if(args.can != None):
    channel = args.can
    args.file = None        # Avoid contradicting channels
elif (args.file != None):
    channel = args.file
else:
    channel = 'can0'

retainall = args.retainall
retaindids = []
if (args.retain != None):
    retaindids_str=args.retain.split(",")
    for did in retaindids_str:
        retaindids.append(eval(did))

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
    if (args.file == None):
        with can.Bus(interface='socketcan',
                    channel=channel,
                    receive_own_messages=True, can_filters=filters) as bus:
            # iterate over received messages
            evalMessages(bus, device, args)
    else:
        import candump2msgbus as dump
        mydump = dump.candump2msgBus(args.file, CANid)
        evalMessages(mydump.file2messages(), device, args)

                                        
except (KeyboardInterrupt, InterruptedError):
    # got <STRG-C> or SIGINT (<kill -s SIGINT pid>)
    pass
