# -*- coding: utf-8 -*-
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

Convert candump file to list of bus messages according to python-can

Supported commands and formats:
    'ts short':     cmnd:       candump -l can0
                    format:     "(1678484087.154260) can0 387#B80100CC0200B801"

    'ts long':      cmnd:       candump -t a can0 > candump.log
                    format:     " (1697695707.985038)  can0  451   [8]  10 12 77 00 00 43 01 82"

    'datetime':     cmnd:       candump -t A can0 > candump.log
                    format:     " (2023-03-12 10:03:51.202750)  can0  5B6   [8]  41 02 41 01 24 00 00 00"

    'simple':       cmnd:       candump can0 > candump.log
                    format:     "  can0  693   [8]  10 0D 77 00 00 43 01 82"

"""

import sys
from datetime import datetime
from can import Bus, message

class candump2msgBus():
    
    def __init__(self, fn, CANid, channel=None):
        self.fn = fn
        self.CANid = CANid
        self.channel = channel

    def line2data(self, line, format):
        parts = line.split(' ')
        if format == 'ts short':
            # format: "(1678484087.154260) can0 387#B80100CC0200B801"
    
            # timestamp
            timestamp_str = parts[0][1:-1]
            ts = float(timestamp_str)
            
            # CAN-ID
            can_id_str = parts[2][:3]
            
            # CAN data
            can_data_str = parts[2][4:-1]
            can_bytes_str = ['','','','','','','','']
            for i in range(0,len(can_data_str)//2):
                can_bytes_str[i] = can_data_str[i*2:i*2+2]
    
        if format == 'ts long':
            # format: " (1697695707.985038)  can0  451   [8]  10 12 77 00 00 43 01 82"
    
            # timestamp
            timestamp_str = parts[1][1:-1]
            ts = float(timestamp_str)
    
            # CAN-ID
            can_id_str = parts[5]
            
            # CAN data
            can_bytes_str = ['','','','','','','','']
            for i in range(10,len(parts)):
                can_bytes_str[i-10] = parts[i][0:2]
    
        if format in  ['datetime','simple']:
            # format datetime: " (2023-03-12 10:03:51.202750)  can0  5B6   [8]  41 02 41 01 24 00 00 00"
            # format simple:   "  can0  693   [8]  10 0D 77 00 00 43 01 82"

            # use datetime if available:
            if format == 'datetime':
                ofs = 0
                ts = datetime.fromisoformat(parts[1][1:]+' '+parts[2][:-1]).timestamp()
            else:
                ofs = -2
                ts = 0
            
            can_id_str = parts[6+ofs]
            can_bytes_str = parts[11+ofs:]
            while len(can_bytes_str) < 8:
                can_bytes_str.append('')
    
        return ts, can_id_str, can_bytes_str
    
    def file2messages(self):
    
        if self.channel != None:
            bus = Bus(interface='socketcan', channel=self.channel)

        # read file and process line by line
        with open(self.fn, 'r') as f:
            lines = f.readlines()
        
        # check for valid file format
        if len(lines[0]) < 4:
            print('File format not recognized. Aborting.')
            sys.exit(0)
        if (lines[0][0:4]==' (20'):
            format = 'datetime'
        elif (lines[0][0]=='('):
            format = 'ts short'
        elif (lines[0][0:2]==' ('):
            format = 'ts long'
        elif (lines[0][0:2]=='  '):
            format = 'simple'
        else:
            print('File format not recognized. Aborting.')
            sys.exit(0)
        
        # init list of messages
        busMessages = []
        
        for line in lines:
            ts, can_id_str, can_bytes_str = self.line2data(line, format)
            data = bytearray()
            can_id = eval('0x'+can_id_str)
            if can_id in self.CANid:
                for b in can_bytes_str:
                    if b>'':
                        data.append(eval('0x'+b))
                msg = message.Message(
                        arbitration_id=can_id,
                        data=data,
                        dlc=len(data),
                        timestamp=float(ts),
                        is_extended_id=False
                      )
                busMessages.append(msg)
                if self.channel != None:
                    bus.send(msg)
        
        if self.channel != None:
            bus.shutdown()

        return busMessages

if __name__ == '__main__':

    test_path     = ''
    test_filename = 'candump.test.log'
    test_CANid    = [0x451]
    test_channel  = None


    # check for args
    if len(sys.argv) > 1:
        text_datei_pfad = sys.argv[1]
    else:
        # use defaults:
        text_datei_pfad = test_path+test_filename

    if len(sys.argv) > 2:
        test_CANid = eval(sys.argv[2])

    if len(sys.argv) > 3:
        test_channel = sys.argv[3]

    conv = candump2msgBus(text_datei_pfad, test_CANid, test_channel)
    messages = conv.file2messages()
#    print(messages)
