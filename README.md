
# tessw
Reads TESS-W data though serial port and publishes to an MQTT broker
To be used in special environments with little or null radio emissions (no WiFi)

## Installation

We will follow an installation example in a virtual environment for a RespberryPi. Using a virtual environment ensures that we don't mess with system Python libraries should we ever mess it up.

Make sure that:
* [*Raspberry Pi OS (32-bit) Lite*](https://www.raspberrypi.org/downloads/raspberry-pi-os/) is installed, 
* You've got a ssh connection and Internet access
* You have Python3 installed.

1. Install Python3 virtual environment support
```bash
pi@astroserver:~ $ sudo apt-get install python3-venv
```

1. Create a virtual environment named `env_tessw`
```bash
pi@astroserver:~ $ python3 -m venv /home/pi/venv_tessw
pi@astroserver:~ $ ls venv_tessw
bin  include  lib  pyvenv.cfg  share
```

1. Activate the virtual environment
```bash
pi@astroserver:~ $ . venv_tessw/bin/activate
(venv_tessw) pi@astroserver:~ $ 
```

1. Install the `tessw-publisher` software within the environment with pip3
```bash
(venv_tessw) pi@astroserver:~ $  pip3 install --user tessw-publisher
```

## Configuration

### The configuration file

1. First, create a subidirectory where to keep the configuration file:

```bash
pi@astroserver:~ $ mkdir /home/pi/venv_tessw/etc
```

1. Then, create a `/home/pi/venv_tessw/etc/config.ini` file taking the contets below as a template

```
# ------------------------------------------------------------------------------
# Copyright (c) 2020 Rafael Gonzalez.
#
# See the LICENSE file for details
# ------------------------------------------------------------------------------

#==============================================================================#
#                            Global configuration Data                         #
#==============================================================================#

[global]

# Transmission period, in seconds
# Not reloadable property
T = 60

# Number of photometers sections below (from 1 to 4)
# Sections below are called [phot1] to [phot4]
# Not reloadable property
nphotom = 1

# component log level (debug, info, warn, error, critical)
# reloadable property
log_level = info

#------------------------------------------------------------------------------#
#                     TESS-W #1 specific configuration Data                    #
#------------------------------------------------------------------------------#

[phot1]


# Write here the true TESS-W MAC address
# Not reloadable property
mac_address = AA:BB:CC:DD:EE:FF

# If old firmware is used, 
# then we need to fill the name and zero point
# parameters below
# Not reloadable property
old_firmware = no

# Unit name. Must match the name assigned by STARS4ALL. 
# Once set, do not change it !!!
# Not reloadable property
name = test1

# Factory-calibrated Zero Point
# if 20.50 is probably uncalibrated
# This is only needed if old_firmware option = yes
# Not reloadable property
zp = 20.50

# Baud rate supported: only 9600
# Not reloadable property
endpoint = serial:/dev/ttyUSB0:9600

# component log level (debug, info, warn, error, critical)
# reloadable property
log_level = info

# log serial protocol messages from/to TESS ?
# reloadable property
log_messages = warn

#==============================================================================#
#                             MQTT configuration Data                          #
#==============================================================================#

[mqtt]

# MQTT Client config

# Broker to connect. Twisted-style endpoint
# Not reloadable property
broker = tcp:test.mosquitto.org:1883


# Username/password credentials
# leave blank if not needed
# non reloadable properies
username = 
password = 

# Keepalive connection (in seconds)
# Not reloadable property
keepalive = 60

# namespace log level (debug, info, warn, error, critical)
# Reloadable property
log_level = info

# MQTT PDUs log level. 
# See all PDU exchanges with 'debug' level. Otherwise, leave it to 'info'
# Reloadable property
log_messages = debug
```

## Running the software

The software can be run in foreground mode in a console for testing purposes. 
With the virtual environment active just type:


```bash
(venv_tessw) pi@astroserver:~ $ tessw --config venv_tessw/etc/config.ini 
```

And the prpogram will show on console some similar to this. 
In this case, there was no photometer attached, so it quits.

```
2020-07-22T07:56:52+0000 [mqtt#info] MQTT Client library version 0.3.9
2020-07-22T07:56:52+0000 [global#info] tessw 0.1.1 on Twisted 20.3.0, Python 3.5
2020-07-22T07:56:52+0000 [supvr#info] starting Supervisor Service
2020-07-22T07:56:52+0000 [phot1#info] starting Photometer Service 1
2020-07-22T07:56:52+0000 [phot1#critical] [Errno 2] could not open port /dev/ttyUSB0: [Errno 2] No such file or directory: '/dev/ttyUSB0'
2020-07-22T07:56:52+0000 [phot1#warn] stopping Photometer Service 1
2020-07-22T07:56:52+0000 [supvr#warn] Will stop the reactor asap.
2020-07-22T07:56:52+0000 [mqttS#info] starting MQTT Client Service
2020-07-22T07:56:52+0000 [mqtt.client.factory.MQTTFactory#info] Starting factory <mqtt.client.factory.MQTTFactory object at 0x75e9c9b0>
2020-07-22T07:56:52+0000 [supvr#info] Getting info from all photometers
2020-07-22T07:56:53+0000 [-] Main loop terminated.
```

However, it has been designed to run as a systemd service. The following section describes how to create this systemd service.

### The systemd file

Place a file named `tesswd.service`  under `/lib/systemd/system` with the following contents:

```
[Unit]
Description=TESS-W Publisher daemon
Documentation=https://github.com/STARS4ALL/tessw-publisher

[Service]
Type=simple
User=pi
KillMode=process
ExecStart=/home/pi/venv_tessw/bin/python3 -m tessw --config /home/pi/venv_tessw/etc/tessw/config.ini --log-file /home/pi/venv_tessw/log/tessw.log
ExecReload=/bin/kill -s HUP -- $MAINPID
EnvironmentFile=/home/pi/tessw.env

[Install]
WantedBy=multi-user.target
```

### The environment file

Create a `/home/pi/tessw.env` file with the following contents:

```bash
PATH=/home/pi/venv_tessw/bin:/usr/local/bin:/usr/bin:/bin
PYTHONIOENCODING=utf-8
VIRTUAL_ENV=/home/pi/venv_tessw/
```

### The logrotate file

1. Create a subidirectory in the virtual environment where to keep log files:

```bash
pi@astroserver:~ $ mkdir /home/pi/venv_tessw/log
```

1. As user `root`, create a `/etc/logrotate.d/tessw` file with a log rotation specification in order to manage daily log files that rotate automatically with the `logrotate` utility, keeping the last 30 days.

```
/home/pi/venv_tessw/log/tessw.log {
	daily
	dateext
	rotate 30
	missingok
	notifempty
	copytruncate
}
```
