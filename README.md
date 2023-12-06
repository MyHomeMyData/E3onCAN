# E3onCAN
* Grab live data on CAN bus of Viessmann E3 series, e.g. Vitocharge VX3, Vitocal 250
* Grab live data on CAN bus of Viessmann energy meter E380 CA
* Only read operations are done on CAN bus. No write operations are possible.
* Decode raw data to physical units for many datapoints
* Optionally send data via MQTT
* Tested so far on external CAN bus of Vitocal 250 connected to Vitocharge VX3 and for E380
* Processing of candumps instead of live data possible
* Based on open3e, see https://github.com/abnoname/open3e.git 

# Requirements
    pip3 install -r requirements.txt

# Setup CAN Bus
    sudo ip link set can0 up type can bitrate 250000

# Usage
    usage: E3onCANcollect.py [-h] [-c CAN] [-dev vx3|vcal|vair|e380] [-canid CANID] [-r READ] [-raw] [-m MQTT] [-mfstr MQTTFORMATSTRING] [-muser MQTTUSER] [-mpass MQTTPASS] [-retain] [-retainall] [-v]

    options:
    -h, --help            show this help message and exit
    -c CAN, --can CAN     use can device, e.g. can0
    -dev dev, --dev dev   device, vx3 or vcal or vair or e380
    -canid CANID, --canid CANID
                          CAN id to listen to, e.g. -canid 0x451, overrides CAN id selected by device
    -r READ, --read READ  read did, e.g. 1690,1834
    -raw, --raw           return raw data for all dids
    -m MQTT, --mqtt MQTT  publish to server, e.g. localhost:1883:topicname
    -mfstr MQTTFORMATSTRING, --mqttformatstring MQTTFORMATSTRING
                          mqtt formatstring e.g. {device}_{didNumber:04d}_{didName}
    -muser MQTTUSER, --mqttuser MQTTUSER
                          mqtt username
    -mpass MQTTPASS, --mqttpass MQTTPASS
                          mqtt password
    -retain dids, --retain dids
   	                      set mqtt retain flag for dids, e.g. 1834,1836
    -retainall, --retainall
   	                      set mqtt retain flag for all dids
    -v, --verbose         verbose info

# Read datapoints
    python3 E3onCANcollect.py -c can0 -dev vx3 -r 1834 -v
    2023-11-15 18:00:37.186155 1834 ElectricalEnergyStorageStateOfEnergy: {"SoC": 3863.0, "Unkown": 0.0}
    2023-11-15 18:00:49.215978 1834 ElectricalEnergyStorageStateOfEnergy: {"SoC": 3858.0, "Unkown": 0.0}
    
    python3 E3onCANcollect.py -c can0 -dev e380 -r 0x250,0x256 -v
    2023-11-15 18:02:49.874932 592 GridActivePower: {"L1": 96.0, "L2": 7.0, "L3": -108.0, "Total": -4.0}
    2023-11-15 18:02:49.878761 598 GridVoltage: {"L1": 233.0, "L2": 234.0, "L3": 233.0, "Frequency": 50.0}
    
# Publish datapoints to mqtt
    python3 E3onCANcollect.py -c can0 -dev vx3 -r 1690,1834 -m localhost:1883:open3e
    -> will decode received datapoints and publish data to broker localhost on topic open3e/did_name

    python3 E3onCANcollect.py -c can0 -dev vx3 -m localhost:1883:open3e -mfstr {device}_{didNumber:04d}_{didName} -retain 1834
    -> will publish **all** received dids with custom identifier format: e.g. open3e/vx3_1690_ElectricalEnergySystemPhotovoltaicStatus
    -> mqtt retain flag for did 1834 will be set

# Convert candump log to datapoints
    candump -t a can0 > candump.log
    python3 E3onCANcollect.py -f candump.log -dev vx3 -canid 0x451 -v
    2023-11-15 14:39:11.046815 378 PointOfCommonCouplingPhaseOne: {"ActivePower": 55.0, "ReactivePower": -119.0}
    2023-11-15 14:39:11.059317 379 PointOfCommonCouplingPhaseTwo: {"ActivePower": -22.0, "ReactivePower": -81.0}
    2023-11-15 14:39:11.073367 380 PointOfCommonCouplingPhaseThree: {"ActivePower": -38.0, "ReactivePower": -89.0}

# E380 data and units

| ID | Data| Unit |
| ------|:--- |------|
| 0x250 | Active Power L1, L2, L3, Total |  W |
| 0x252 | Reactive Power L1, L2, L3, Total | W |
| 0x254 | Current, L1, L2, L3, cosPhi | A, - |
| 0x256 | Voltage, L1, L2, L3, Frequency | V, Hz |
| 0x258 | Cumulated Import, Export | kWh |
| 0x25A | Total Active Power, Total Reactive Power | W |
| 0x25C | Cumulated Import | kWh |

# Limitations, Hints
* Scans for available data on CAN bus, no active request for data as with open3e.
* Works best on external CAN bus of Vitocal 250 when connected to Vitocharge VX3 via external bus.
* Data is typically updated by E3 device on change of value.
* Data of slave device (e.g. VX3) typically is available on external CAN, data of master device (e.g. Vitocal) typically is available on internal CAN
* Will probably not work on stand alone devices. See open3e for this case.
* Works for energy meter E380 on stand alone VX3 configuration.
* For E380 datapoints ids are set equal to CAN ids. CAN ids are restricted to 0x250,0x252,0x254,0x256,0x258,0x25A,0x25C
* To scan more than one device at the same time, start one instance for each device