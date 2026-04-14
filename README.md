# E3onCAN

E3onCAN passively reads data from the CAN bus of Viessmann E3 series devices (e.g. Vitocal 250, Vitocharge VX3) and Viessmann energy meters (E380 CA, E3100CB). Received raw data is decoded and output as physical values — either to the terminal or via MQTT to a broker. No write operations are performed on the CAN bus.

The project is based on [open3e](https://github.com/abnoname/open3e.git) and extends it by passively listening to the so-called "Collect" protocol, which Viessmann E3 devices broadcast unsolicited on the CAN bus.

## Supported Devices

| Device | Type | Description |
|---|---|---|
| Vitocal 250 | `vcal` | Heat pump |
| Vitocharge VX3 | `vx3` | Battery storage |
| Vitoair | `vair` | Ventilation unit |
| Vitodensxxx | `vdens` | Gas heating |
| E380 CA | `e380` | Energy meter |
| E3100CB | `e3100cb` | Energy meter |

## What's new in V0.5.0

### Variant data points replace device-specific data point files

Previous versions handled differences between E3 device types (Vitocal,
Vitocharge VX3, Vitoair, Vitodensxxx) by maintaining separate data point
files per device (`Open3EdatapointsVx3.py`, `Open3EdatapointsVcal.py`, etc.).
At startup, the general data point table was loaded and then overlaid with
device-specific overrides or deletions.

V0.5.0 adopts the **variant data point** concept introduced in open3e v0.6.0.
Instead of per-device tables, a single file `Open3EdatapointsVariants.py`
lists alternative codec definitions keyed by **DID and payload length**. At
runtime, the correct codec is selected automatically based on the actual
number of bytes received for a given DID — no prior knowledge of the connected
device type is required.

The internal DID lookup key changed from `DID` (integer) to `DID.length`
(e.g. `"1603.8"` or `"1603.12"`), allowing the same DID to be decoded
differently depending on the payload length sent by the device on the bus.

**What this means in practice:**
- The device-specific files `Open3EdatapointsVx3.py`, `Open3EdatapointsVcal.py`,
  `Open3EdatapointsVair.py` and `Open3EdatapointsVdens.py` are no longer used
  and can be removed.
- The `-dev` parameter still selects the CAN-ID to listen to and switches
  between E3 devices and energy meters, but no longer controls which data
  points are available.
- Multiple E3 device types on the same CAN bus are decoded correctly without
  any configuration change.

### Reference list of all known data points

[Open3Edatapoints.md](Open3Edatapoints.md) is a new reference document listing
all currently known data points, many with a short description, unit, access
mode (read-only / read-write), and links to further information. It covers both
the common data points and the variant definitions.

### Improved Docker support

The Docker setup has been reworked. Two ready-to-use compose files are now
provided in the project root:

- **`compose.yml`** — for end users: builds the image by cloning the latest
  E3onCAN release from GitHub. No local repository required, update with a
  single `docker compose build --no-cache`.
- **`compose.dev.yml`** — for developers: builds the image from the local
  project files, useful for testing changes before pushing.

See [Docker/README.md](Docker/README.md) for full instructions.

## Installation

For a fresh Raspberry Pi installation, first install git, python3 and pip:
```
sudo apt install git python3 python3-pip
```
It's strongly recommended to create a virtual environment. To install into folder `~/e3`:
```
sudo apt install python3-virtualenv
mkdir ~/e3 && cd ~/e3
python3 -m venv .venv && source .venv/bin/activate
git clone https://github.com/MyHomeMyData/E3onCAN.git
cd E3onCAN
pip3 install -r requirements.txt
```
Check that it's working: `python3 E3onCANcollect.py -h` should show the help text.

To deactivate the virtual environment: `deactivate`

To activate it again: `cd ~/e3/E3onCAN && source ../.venv/bin/activate`

Setting up E3onCAN as a system service is also possible, see [Setting up a system service](#setting-up-a-system-service).

### Updating to the latest version

```
cd ~/e3/E3onCAN
git pull
source ../.venv/bin/activate
pip3 install -r requirements.txt
```

> **Note:** After updating, always update the dependent packages as well (`pip3 install -r requirements.txt`).

## Setup CAN Bus

```
sudo ip link set can0 up type can bitrate 250000
```

## Usage

```
usage: E3onCANcollect.py [-h] [-c CAN] [-f FILE] [-dev DEV] [-canid CANID]
                         [-r READ] [-raw] [-g GAP]
                         [-m MQTT] [-mfstr MQTTFORMATSTRING] [-muser MQTTUSER] [-mpass MQTTPASS]
                         [-retain DIDS] [-retainall] [-v]

options:
  -h, --help                          show this help message and exit
  -c CAN, --can CAN                   use CAN device, e.g. can0
  -f FILE, --file FILE                use candump file as input, e.g. candump.log
  -dev DEV, --dev DEV                 device type: vcal | vx3 | vair | vdens | e380 | e3100cb
  -canid CANID, --canid CANID         CAN ID to listen to, e.g. 0x451 (overrides device default)
  -r READ, --read READ                only decode specific DIDs, e.g. 1690,1834
  -raw, --raw                         output raw hex data instead of decoded values
  -g GAP, --gap GAP                   minimum time gap (seconds) between decodings of the same DID
  -m MQTT, --mqtt MQTT                MQTT broker, e.g. localhost:1883:topicname
  -mfstr MFSTR, --mqttformatstring    MQTT topic format string, e.g. {device}_{didNumber:04d}_{didName}
  -muser MUSER, --mqttuser MUSER      MQTT username
  -mpass MPASS, --mqttpass MPASS      MQTT password
  -retain DIDS, --retain DIDS         set MQTT retain flag for specific DIDs, e.g. 1834,1836
  -retainall, --retainall             set MQTT retain flag for all DIDs
  -v, --verbose                       verbose output
```

## Examples

### Read data points (terminal output)

```
python3 E3onCANcollect.py -c can0 -dev vx3 -r 1834 -v
2023-11-15 18:00:37.186155 1834 ElectricalEnergyStorageStateOfEnergy: {"SoC": 3863.0, "Unkown": 0.0}
2023-11-15 18:00:49.215978 1834 ElectricalEnergyStorageStateOfEnergy: {"SoC": 3858.0, "Unkown": 0.0}
```

```
python3 E3onCANcollect.py -c can0 -dev e380 -r 0x250,0x256 -v
2023-11-15 18:02:49.874932 592 GridActivePower: {"L1": 96.0, "L2": 7.0, "L3": -108.0, "Total": -4.0}
2023-11-15 18:02:49.878761 598 GridVoltage: {"L1": 233.0, "L2": 234.0, "L3": 233.0, "Frequency": 50.0}
```

### Publish data points via MQTT

```
python3 E3onCANcollect.py -c can0 -dev vx3 -r 1690,1834 -m localhost:1883:open3e
```
Decodes received data points and publishes them to broker `localhost` under topic `open3e/<didName>`.

```
python3 E3onCANcollect.py -c can0 -dev vx3 -m localhost:1883:open3e -mfstr {device}_{didNumber:04d}_{didName} -retain 1834
```
Publishes **all** received DIDs with a custom topic format, e.g. `open3e/vx3_1690_ElectricalEnergySystemPhotovoltaicStatus`. The retain flag is set for DID 1834.

### Process a candump log file

```
candump -t a can0 > candump.log
python3 E3onCANcollect.py -f candump.log -dev vx3 -canid 0x451 -v
2023-11-15 14:39:11.046815 378 PointOfCommonCouplingPhaseOne: {"ActivePower": 55.0, "ReactivePower": -119.0}
2023-11-15 14:39:11.059317 379 PointOfCommonCouplingPhaseTwo: {"ActivePower": -22.0, "ReactivePower": -81.0}
2023-11-15 14:39:11.073367 380 PointOfCommonCouplingPhaseThree: {"ActivePower": -38.0, "ReactivePower": -89.0}
```

## Energy Meter Data Points

### E380 CA

Up to two E380 energy meters are supported. DID numbers depend on the device's CAN address:
- CAN address 97 → even IDs (default configuration)
- CAN address 98 → odd IDs

| ID | Data | Unit |
|---|---|---|
| 592, 593 | Active Power L1, L2, L3, Total | W |
| 594, 595 | Reactive Power L1, L2, L3, Total | VA |
| 596, 597 | Current L1, L2, L3, cosPhi | A, - |
| 598, 599 | Voltage L1, L2, L3, Frequency | V, Hz |
| 600, 601 | Cumulated Import, Export | kWh |
| 602, 603 | Total Active Power, Total Reactive Power | W, VA |
| 604, 605 | Cumulated Import | kWh |

### E3100CB

| ID | Data | Unit |
|---|---|---|
| 1385.01 | Cumulated Import | kWh |
| 1385.02 | Cumulated Export | kWh |
| 1385.03 | State: -1 = feed-in, +1 = supply | - |
| 1385.04 | Active Power Total | W |
| 1385.08 | Active Power L1 | W |
| 1385.12 | Active Power L2 | W |
| 1385.16 | Active Power L3 | W |
| 1385.05 | Reactive Power Total | var |
| 1385.09 | Reactive Power L1 | var |
| 1385.13 | Reactive Power L2 | var |
| 1385.17 | Reactive Power L3 | var |
| 1385.06 | Current, Absolute L1 | A |
| 1385.10 | Current, Absolute L2 | A |
| 1385.14 | Current, Absolute L3 | A |
| 1385.07 | Voltage L1 | V |
| 1385.11 | Voltage L2 | V |
| 1385.15 | Voltage L3 | V |

## Hints and Limitations

* **Read-only:** Only read operations are performed on the CAN bus — no write operations.
* E3onCAN passively waits for data (no active polling like open3e).
* Works best on the external CAN bus of a Vitocal 250 connected to a Vitocharge VX3.
* Data from the slave device (e.g. VX3) is typically available on the external CAN bus; data from the master device (e.g. Vitocal) is typically available on the internal CAN bus.
* Will probably not work on stand-alone devices without a connection to another E3 device — use open3e for that case.
* Works for the E380 energy meter in a stand-alone VX3 configuration.
* To monitor more than one device simultaneously, start one instance per device.

## Setting up a System Service

E3onCAN can be set up as a systemd service that starts automatically on system boot.

The following steps assume the installation in `~/e3` described above. For a general guide see also the [open3e documentation](https://github.com/open3e/open3e/wiki/030-Installation-und-Inbetriebnahme-von-open3E#open3e-als-service-einrichten-und-bei-systemstart-automatisch-starten).

**Create the service description file:**

```
sudo nano /lib/systemd/system/e3oncan.service
```

Insert the following content (adapt the command line parameters to your needs), then save and close (`<CTRL>-O` `<CTRL>-X`):

```ini
[Unit]
Description=E3onCAN Service Script
After=multi-user.target

[Service]
Type=simple
ExecStartPre=/bin/sleep 5
Restart=on-failure
User=pi
ExecStart=/bin/bash -c 'cd /home/pi/e3/E3onCAN && source /home/pi/e3/.venv/bin/activate && python3 /home/pi/e3/E3onCAN/E3onCANcollect.py -c can0 -dev vcal -m localhost:1883:open3e/vcal -mfstr {device}_{didNumber:04d}_{didName}'

[Install]
WantedBy=multi-user.target
```

The 5-second delay (`ExecStartPre=/bin/sleep 5`) ensures the CAN adapter is ready before E3onCAN starts. Increase this value if problems occur.

**Set permissions and activate the service:**

```
sudo chmod 644 /lib/systemd/system/e3oncan.service
sudo systemctl daemon-reload
sudo systemctl enable e3oncan.service
sudo systemctl start e3oncan.service
```

**Check status:**

```
systemctl status e3oncan.service
```

**Other useful commands:**

```
sudo systemctl stop e3oncan.service      # stop the service
sudo systemctl restart e3oncan.service   # restart the service
sudo systemctl disable e3oncan.service   # disable autostart
```

## Docker

A Docker version is also available, see [Docker/README.md](Docker/README.md).

## Donate

<a href="https://www.paypal.com/donate/?hosted_button_id=WKY6JPYJNCCCQ"><img src="https://raw.githubusercontent.com/MyHomeMyData/E3onCAN/main/bluePayPal.svg" height="40"></a>  
If you enjoyed this project — or just feeling generous, consider buying me a beer. Cheers! :beers:

## Changelog

<!--
    Placeholder for the next version (at the beginning of the line):
    ### **WORK IN PROGRESS**
-->

### 0.5.0 (2026-04-14)
* (MyHomeMyData) Updated list of data points to version 20260227 (common) and 20260217 (variants)
* (MyHomeMyData) Data point handling has been switched to variant data points, see project open3e from v0.6.0 onwards
* (MyHomeMyData) Added list of known data points as markdown file
* (MyHomeMyData) Docker setup has been reworked

### 0.4.5 (2025-11-12)
* (MyHomeMyData) Updated list of data points to version 20251102
* (MyHomeMyData) Added version info to help text
* (MyHomeMyData) Added hint regarding update procedure to Readme

### 0.4.4 (2025-09-23)
* (MyHomeMyData) Updated list of data points to version 20250903
* (MyHomeMyData) Removed device specific data point definitions for vdens on data points 381 and 401 to 404
* (MyHomeMyData) Adapted how-to about setting up a system service to new behaviour of venv

### 0.4.3 (2025-05-22)
* (MyHomeMyData) Updated list of data points to version 20250422

### 0.4.2 (2024-02-19)
* (MyHomeMyData) Updated list of data points to version 20250208
* (MyHomeMyData) Removed obsolete parameter 'offset' from codecs
* (MyHomeMyData) Added asserts to ensure length of data point definitions

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
