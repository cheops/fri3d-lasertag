#heavily inspired on https://github.com/Fri3dCamp/Fri3dBadge/blob/master/bin/defaultFirmware/flash.py
import sys
import glob
import subprocess

from serial.tools import list_ports

VID = 4292
PID = 60000

def get_serial():
    device_list = list_ports.comports()
    devices = list()
    for device in device_list:
        if (device.vid != None or device.pid != None):
            if (device.vid == VID and
                device.pid == PID):
                    #print('found port ' + device.device)
                    devices.append(device)
                    
    return devices
    
last_run = list()
while True:
    this_run = get_serial()
    for port in this_run:
        #print(port)
        if port not in last_run:
            subprocess.Popen([r"python", "-m", "esptool", "-p", port.device, "-b", "460800", "--before", "default_reset", "--after", "hard_reset", "--chip", "esp32",  "write_flash", "--flash_mode", "dio", "--flash_size",  "detect", "-flash_freq",  "40m", "0x1000", "bootloader.bin", "0x8000", "partition-table.bin", "0x10000", "micropython.bin"])
    last_run = this_run
    