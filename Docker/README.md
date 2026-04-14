# E3onCAN on Docker

E3onCAN can be run as a Docker container. Two workflows are supported:

| Workflow | For whom | Compose file |
|---|---|---|
| **Standard** — builds image by cloning latest E3onCAN from GitHub | End users | `compose.yml` |
| **Dev** — builds image from local project files | Developers | `compose.dev.yml` |

Both compose files are located in the **project root**.

---

## Prerequisites

### Set up the CAN interface on the host

The CAN adapter must be configured on the host before starting the container.
The container accesses the CAN bus via `network_mode: host`, which shares the
host's full network stack (including SocketCAN interfaces) with the container.
No device mapping is required.

Follow the best practices for persistently naming your USB CAN adapter:
https://github.com/open3e/open3e/blob/master/bestPractices/USB%20Adapter%20and%20udev.md

Then bring up the CAN interface (e.g. on every boot via a systemd service or
`/etc/network/interfaces`):

```
sudo ip link set can0 up type can bitrate 250000
```

---

## Standard usage (end users)

The standard `compose.yml` builds the Docker image by cloning the latest
version of E3onCAN directly from GitHub. No local clone of the repository is
required.

**1. Get the compose file**

Download `compose.yml` from the repository root to your machine:

```
curl -O https://raw.githubusercontent.com/MyHomeMyData/E3onCAN/main/compose.yml
```

Or simply copy the file manually.

**2. Adapt `CLI_ARGS`**

Edit `compose.yml` and set `CLI_ARGS` to match your setup. Examples:

```
# E3 device (heat pump, battery storage, etc.) with MQTT output:
CLI_ARGS: "-c can0 -dev vcal -m localhost:1883:open3e -mfstr {device}_{didNumber:04d}_{didName}"

# Energy meter E380 with MQTT output:
CLI_ARGS: "-c can0 -dev e380 -m localhost:1883:open3e"

# Terminal output only (no MQTT):
CLI_ARGS: "-c can0 -dev vcal -v"
```

See the [main README](../README.md) for a full description of all options.

**3. Build and start**

```
docker compose -f compose.yml build
docker compose -f compose.yml up -d
```

**To update to a newer version**, rebuild the image:

```
docker compose -f compose.yml build --no-cache
docker compose -f compose.yml up -d
```

---

## Developer usage

The `compose.dev.yml` builds the image from the local project files instead
of cloning from GitHub. Use this when you want to test local changes before
pushing them.

**Build and start from local source:**

```
docker compose -f compose.dev.yml build
docker compose -f compose.dev.yml up -d
```

After modifying local files, rebuild to pick up the changes:

```
docker compose -f compose.dev.yml build
docker compose -f compose.dev.yml up -d
```

---

## Useful commands

```
# Show running containers
docker compose -f compose.yml ps

# Follow log output
docker compose -f compose.yml logs -f

# Stop the container
docker compose -f compose.yml down

# Restart the container
docker compose -f compose.yml restart
```

---

## How the CAN bus access works

Linux implements CAN adapters as network interfaces (SocketCAN), not as device
files. Setting `network_mode: host` in the compose file gives the container
access to the host's entire network namespace — including all CAN interfaces
such as `can0`. No `--privileged` flag or `/dev` mapping is needed.

The same `network_mode: host` setting also allows the container to reach an
MQTT broker running on `localhost` of the host machine.
