# Why this fork?
I have a HA core installation on a rpi3 with a dietpi distro and 3 Danfoss thermostats. 
During the installation of etrv2mqtt with uv I got an error msg that bluepy couln't
get build. After some search I discovered, that bluepy is not compatible with python > 3.7 
and not activly maintained. But there is bluepy3 a modern drop in for bluepy.
So I try to see if libetrv works with bluepy3 and can installed with uv.

# libetrv


**Library is currently under development and it is not design to be used by end user**

Monitor and control your eTRV from Python. Recently Danfoss has released new TRVs that can be controlled
over Bluetooth Low Energy. This library will allow connect this devices and control them.

Application was developed on a Raspberry Pi  B+, but should work fine on any Linux based system with Bluetooth LE device.

## Supported Devices

All supported and tested devices:

- Danfoss Eco Bluetooth LE - WIP

## Changelog

### Version 0.6
- Migrated CI/CD processes to GitHub Actions workflows.
- Updated the minimum required Python version to 3.9.
- Updated setup scripts to use `setuptools`.
- Added functionality to set the pin number for devices.
- Updated README with new installation instructions and usage examples.
- Removed outdated CircleCI badge from the README.

## Installation
This software requires at least Python 3.5. All required packages are listed in file `requirements.txt`.

Because software is under development there is no direct way to install it on system and setup it as system service.

For development just create virtual env and install all requirements.

```bash
$ mkdir -p ~/venv/libetrv
$ python3 -m venv ~/venv/libetrv
$ source ~/venv/libetrv/bin/activate
$ pip3 install -r requirements.txt
```
  

## Bluetooth Permissions
It is recommended to not start this app as `root` user. To avoid this you can allow python3 to access to Bluetooth interface

```bash
$ sudo apt-get install libcap2-bin
$ sudo setcap 'cap_net_raw,cap_net_admin+eip' `readlink -f \`which python3\``
$ sudo setcap 'cap_net_raw+ep' `readlink -f \`which hcitool\``
```
