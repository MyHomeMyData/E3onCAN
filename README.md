# E3onCAN
* Grab live data on CAN bus of Viessmann E3 series, e.g. Vitocharge VX3, Vitocal 250
* Scan for specified datapoints on CAN bus. Does only read operations on bus.
* Decode raw data to physical units
* Optionaly send data via MQTT
* Tested so far on external CAN bus of Vitocal 250 connected to Vitocharge VX3
* Based on https://github.com/abnoname/open3e.git 

# Requirements
    pip3 install -r requirements.txt

# Setup CAN Bus
    sudo ip link set can0 up type can bitrate 250000

# Usage
    usage: E3onCAN.py [-h] [-c CAN] [-r READ] [-m MQTT] [-mfstr MQTTFORMATSTRING] [-muser MQTTUSER] [-mpass MQTTPASS] [-v]

    options:
    -h, --help            show this help message and exit
    -c CAN, --can CAN     use can device, e.g. can0
    -r READ, --read READ  read did, e.g. 0x173,0x174
    -m MQTT, --mqtt MQTT  publish to server, e.g. 192.168.0.1:1883:topicname
    -mfstr MQTTFORMATSTRING, --mqttformatstring MQTTFORMATSTRING
                            mqtt formatstring e.g. {didNumber}_{didName}
    -muser MQTTUSER, --mqttuser MQTTUSER
                            mqtt username
    -mpass MQTTPASS, --mqttpass MQTTPASS
                            mqtt password
    -v, --verbose         verbose info

# Read dids
    python3 E3onCAN.py -c can0 -r 1690,1834 -v
    1690 ElectricalEnergySystemPhotovoltaicStatus 42.0
    1834 ElectricalEnergyStorageStateOfEnergy 14500.0

# Publish datapoints to mqtt
    python3 E3onCAN.py -c can0 -r 1690,1834 -m localhost:1883:open3e
    -> will decode received datapoints and publish data to broker localhost on topic open3e/did_name

    python3 E3onCAN.py -c can0 -r 1690,1834 -m localhost:1883:open3e -mfstr {didNumber:04d}_{didName}
    -> will publish with custom identifier format: e.g. open3e/1690_ElectricalEnergySystemPhotovoltaicStatus

# Restrictions
* Scans for available data on CAN bus, no active request for data as with open3e.
* Works best on external CAN bus of Vitocal 250 when connected to Vitocharge VX3 via external bus.
* Will probably not work on stand alone VX3. See open3e for this case.
