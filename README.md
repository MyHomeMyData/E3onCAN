# E3onCAN
* Grab live data on CAN bus of Viessmann E3 series, e.g. Vitocharge VX3, Vitocal 250
* Grab live data on CAN bus of Viessmann energy meter E380 CA (up to two devices)
* Grab live data on CAN bus of Viessmann energy meter E3100CB
* Only read operations are done on CAN bus. No write operations are possible.
* Decode raw data to physical units for many data points
* Optionally send data via MQTT
* Tested so far on external CAN bus of Vitocal 250 connected to Vitocharge VX3, for E380 and for E3100CB
* Processing of candumps instead of live data possible
* Based on open3e, see https://github.com/abnoname/open3e.git
* A version for [Docker](Docker/README.md) is also available.

# Installation
For a fresh Raspberry PI install git, python3 and python-pip first:
```
sudo apt install git python3 python3-pip
```
It's strongly recommended to create a virtual environment to install E3onCAN. To do a install to folder `~/e3` follow these steps:
```
sudo apt install python3-virtualenv
mkdir ~/e3 && cd ~/e3
python3 -m venv .venv && source .venv/bin/activate
git clone https://github.com/MyHomeMyData/E3onCAN.git
cd E3onCAN
pip3 install -r requirements.txt
```
Check, if it's working: `python3 E3onCANcollect.py -h` should show the help text.

To deactivate venv Environment, simply use `deactivate`.

To activate venv again use `cd ~/e3/E3onCAN && source ../.venv/bin/activate`

It's also possible to setup the task as a service. Please refer to explanations given [here](https://github.com/open3e/open3e/wiki/030-Installation-und-Inbetriebnahme-von-open3E#open3e-als-service-einrichten-und-bei-systemstart-automatisch-starten).
Of course of have to adapt folders and commands for E3onCAN accordingly.

# Setup CAN Bus
    sudo ip link set can0 up type can bitrate 250000

# Usage
    usage: E3onCANcollect.py [-h] [-c CAN] [-dev vx3|vcal|vair|e380|e3100cb] [-canid CANID] [-r READ] [-raw] [-m MQTT] [-mfstr MQTTFORMATSTRING] [-muser MQTTUSER] [-mpass MQTTPASS] [-retain] [-retainall] [-v]

    options:
    -h, --help            show this help message and exit
    -c CAN, --can CAN     use can device, e.g. can0
    -dev dev, --dev dev   device, vx3 or vcal or vair or e380 or e3100cb
    -canid CANID, --canid CANID
                          CAN ID to listen to, e.g. -canid 0x451, overrides CAN ID selected by device
    -r READ, --read READ  read did, e.g. 1690,1834
    -raw, --raw           return raw data for all dids
    -g, --gap             minimum time gap (seconds) between decoding of specific dids.
                          Default: 0 => immediate decoding.
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

# Read data points
    python3 E3onCANcollect.py -c can0 -dev vx3 -r 1834 -v
    2023-11-15 18:00:37.186155 1834 ElectricalEnergyStorageStateOfEnergy: {"SoC": 3863.0, "Unkown": 0.0}
    2023-11-15 18:00:49.215978 1834 ElectricalEnergyStorageStateOfEnergy: {"SoC": 3858.0, "Unkown": 0.0}
    
    python3 E3onCANcollect.py -c can0 -dev e380 -r 0x250,0x256 -v
    2023-11-15 18:02:49.874932 592 GridActivePower: {"L1": 96.0, "L2": 7.0, "L3": -108.0, "Total": -4.0}
    2023-11-15 18:02:49.878761 598 GridVoltage: {"L1": 233.0, "L2": 234.0, "L3": 233.0, "Frequency": 50.0}
    
# Publish data points to mqtt
    python3 E3onCANcollect.py -c can0 -dev vx3 -r 1690,1834 -m localhost:1883:open3e
    -> will decode received data points and publish data to broker localhost on topic open3e/did_name

    python3 E3onCANcollect.py -c can0 -dev vx3 -m localhost:1883:open3e -mfstr {device}_{didNumber:04d}_{didName} -retain 1834
    -> will publish **all** received dids with custom identifier format: e.g. open3e/vx3_1690_ElectricalEnergySystemPhotovoltaicStatus
    -> mqtt retain flag for did 1834 will be set

# Convert candump log to data points
    candump -t a can0 > candump.log
    python3 E3onCANcollect.py -f candump.log -dev vx3 -canid 0x451 -v
    2023-11-15 14:39:11.046815 378 PointOfCommonCouplingPhaseOne: {"ActivePower": 55.0, "ReactivePower": -119.0}
    2023-11-15 14:39:11.059317 379 PointOfCommonCouplingPhaseTwo: {"ActivePower": -22.0, "ReactivePower": -81.0}
    2023-11-15 14:39:11.073367 380 PointOfCommonCouplingPhaseThree: {"ActivePower": -38.0, "ReactivePower": -89.0}

# E380 data and units
Up to two E380 energy meters are supported. IDs of data points depends on devices CAN address:

CAN-address=97: data points with even IDs (default configuration)

CAN-address=98: data points with odd IDs

| ID | Data| Unit |
| ------|:--- |------|
| 592,593 | Active Power L1, L2, L3, Total |  W |
| 594,595 | Reactive Power L1, L2, L3, Total | VA |
| 596,597 | Current, L1, L2, L3, cosPhi | A, - |
| 598,599 | Voltage, L1, L2, L3, Frequency | V, Hz |
| 600,601 | Cumulated Import, Export | kWh |
| 602,603 | Total Active Power, Total Reactive Power | W, VA |
| 604,605 | Cumulated Import | kWh |

# E3100CB data and units

| ID | Data| Unit |
| ------|:--- |------|
| 1385.01 | Cumulated Import | kWh |
| 1385.02 | Cumulated Export | kWh |
| 1385.03 | State: -1 => feedin \| +1 => supply | |
| 1385.04 | Active Power Total |  W |
| 1385.08 | Active Power L1 |  W |
| 1385.12 | Active Power L2 |  W |
| 1385.16 | Active Power L3 |  W |
| 1385.05 | Reactive Power Total | var |
| 1385.09 | Reactive Power L1 | var |
| 1385.13 | Reactive Power L2 | var |
| 1385.17 | Reactive Power L3 | var |
| 1385.06 | Current, Absolute L1 | A |
| 1385.10 | Current, Absolute L2 | A |
| 1385.14 | Current, Absolute L3 | A |
| 1385.07 | Voltage, L1 | V |
| 1385.11 | Voltage, L2 | V |
| 1385.15 | Voltage, L3 | V |

# Limitations, Hints
* **Important:** After updating to new version pls. apply an update also to dependet packages: `pip3 install -r requirements.txt`
* Scans for available data on CAN bus, no active request for data as with open3e.
* Works best on external CAN bus of Vitocal 250 when connected to Vitocharge VX3 via external bus.
* Data is typically updated by E3 device on change of value.
* Data of slave device (e.g. VX3) typically is available on external CAN, data of master device (e.g. Vitocal) typically is available on internal CAN
* Will probably not work on stand alone devices. See open3e for this case.
* Works for energy meter E380 on stand alone VX3 configuration.
* For E380 data point IDs are set equal to CAN IDs. CAN IDs are restricted to the range of 0x250 .. 0x25D (592 .. 605) related to CAN-adresses of 97 (even IDs) and 98 (odd IDs).
* To scan more than one device at the same time, start one instance for each device

## Changelog
<!--
    Placeholder for the next version (at the beginning of the line):
    ### **WORK IN PROGRESS**
-->

### 0.4.1 (2024-11-26)
* (MyHomeMyData) Updated list of data points to version 20241125

### 0.4.0 (2024-04-24)
* (MyHomeMyData) Added -g option to specify minimum time gap between decodings
* (MyHomeMyData) Updated list of data points to version 20240505
* (MyHomeMyData) Added info for data points 2404_BivalenceControlMode and 2831_BivalenceControlAlternativeTemperature

### 0.3.1 (2024-04-20)
* (MyHomeMyData) Structure of ID 1690 (ElectricalEnergySystemPhotovoltaicStatus) changed based on issue #6

### 0.3.0 (2024-04-18)
* (MyHomeMyData) Main change for id 0x258/0x259 (GridEnergy): Now using correct data format. Many thanks to @M4n197 for unveiling the right data format.
* (MyHomeMyData) Added support for energy meter E3100CB. Many thanks to @pellenbeck and @rtr1001 for valuable contributions.

### 0.2.0 (2024-03-21)
* (MyHomeMyData) Added support for E380 with CAN-address=98

### 0.1.0 (2023-10-17)
* (MyHomeMyData) Initial version
