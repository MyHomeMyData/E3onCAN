E3onCAN on Docker

This folder contains the Dockerfile to create your on Docker image for E3onCAN. 

There is a Raspberry Pi 4 image available on docker hub `docker pull fleckem/e3oncan` Please note this is only an ARM64 image and tested on the Raspberry Pi 4. It might work on other ARM64 based systems.

Before running the images you should follow the best practices to peristently map the CAN adapter example on: https://github.com/open3e/open3e/blob/master/bestPractices/USB%20Adapter%20and%20udev.md 

Example of a simple docker compose file for running E3onCAN in Docker:

Please adjust the CLI_ARGS according to the documentation on https://github.com/MyHomeMyData/E3onCAN

```
services:
  e3oncan:
    container_name: e3oncan
    image: "fleckem/e3oncan"
	  network_mode: "host"
    environment:
      CLI_ARGS: "-c can0 -dev e380"
    restart: always
```
