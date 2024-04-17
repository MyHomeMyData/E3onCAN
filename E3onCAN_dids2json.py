#
# Convert datapoint list for E380 and E3100CB to JSON format, e.g. for use in ioBroker adapter E3onCAN
#

import json
from datetime import date

import E3onCANdatapointsE380
from E3onCANdatapointsE380 import *

import E3onCANdatapointsE3100CB
from E3onCANdatapointsE3100CB import *

def dids2json(ids, fname, ver):
    cntDps = 0
    didsDict = {}

    for dp in ids:
        didsDict[dp] = ids[dp].getCodecInfo()
        cntDps += 1

    didsDict['Version'] = ver

    with open(fname+'.json', 'w') as json_file:
        json.dump(didsDict, json_file, indent=2)

    print(str(cntDps)+' dids converted to JSON format. See file "'+fname+'.json"')

# MAIN
# ====

print('Start conversion of datapoints for energy meters to json format.\n')
didsListVersion = date.today().strftime("%Y%m%d")

dids2json(dict(E3onCANdatapointsE380.dataIdentifiersE380), 'E3onCANdatapointsE380', didsListVersion)
dids2json(dict(E3onCANdatapointsE3100CB.dataIdentifiersE3100CB), 'E3onCANdatapointsE3100CB', didsListVersion)

print('\nDone.')
