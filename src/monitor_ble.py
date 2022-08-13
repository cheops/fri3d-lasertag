# This example finds and connects to a BLE temperature sensor (e.g. the one in ble_temperature.py).

import uasyncio
import bluetooth
import random
import struct
import time
import re

from ble_advertising import decode_services, decode_name

from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)

# org.bluetooth.service.lasertag
#_LASERTAG_UUID = bluetooth.UUID(0x936b6a25-e503-4f7c-9349-bcc76c22b8c3)
_LASERTAG_UUID = bluetooth.UUID(0x936b)
# org.bluetooth.characteristic.start
#_START_UUID = bluetooth.UUID(0xc20a0897-117d-4ddf-b035-deb2d3ce65a9)
_START_UUID = bluetooth.UUID(0xc20a)
_START_CHAR = (_START_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,)
_GAME_UUID = bluetooth.UUID(0xc20b)
_GAME_CHAR = (_GAME_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,)
_LASERTAG_SERVICE = (_LASERTAG_UUID, (_START_CHAR,),)

# org.bluetooth.characteristic.gap.appearance.xml
#_ADV_APPEARANCE_GENERIC_THERMOMETER = const(768)


class BLELasertagCentral:
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)

        self._reset()

    def _reset(self):
        # Cached name and address from a successful scan.
        self._name = None
        self._addr_type = None
        self._addr = None

        # Cached value (if we have one)
        self._value = None

        # Callbacks for completion of various operations.
        # These reset back to None after being invoked.
        self._scan_callback = None
        self._conn_callback = None
        self._read_callback = None

        # Persistent callback for when new data is notified from the device.
        self._notify_callback = None

        # Connected device.
        self._conn_handle = None
        self._start_handle = None
        self._end_handle = None
        self._value_handle = None

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND) and _LASERTAG_UUID in decode_services(adv_data):
                # Found a potential device, remember it and stop scanning.
                print("adv_data", adv_data)
                self._addr_type = addr_type
                self._addr = bytes(addr)  # Note: addr buffer is owned by caller so need to copy it.
                self._name = decode_name(adv_data) or "?"
                self._ble.gap_scan(None)

        elif event == _IRQ_SCAN_DONE:
            if self._scan_callback:
                if self._addr:
                    # Found a device during the scan (and the scan was explicitly stopped).
                    self._scan_callback(self._addr_type, self._addr, self._name)
                    self._scan_callback = None
                else:
                    # Scan timed out.
                    self._scan_callback(None, None, None)

        elif event == _IRQ_PERIPHERAL_CONNECT:
            # Connect successful.
            conn_handle, addr_type, addr = data
            if addr_type == self._addr_type and addr == self._addr:
                self._conn_handle = conn_handle
                self._ble.gattc_discover_services(self._conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Disconnect (either initiated by us or the remote end).
            conn_handle, _, _ = data
            if conn_handle == self._conn_handle:
                # If it was initiated by us, it'll already be reset.
                self._reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Connected device returned a service.
            conn_handle, start_handle, end_handle, uuid = data
            if conn_handle == self._conn_handle and uuid == _LASERTAG_UUID:
                self._start_handle, self._end_handle = start_handle, end_handle

        elif event == _IRQ_GATTC_SERVICE_DONE:
            # Service query complete.
            if self._start_handle and self._end_handle:
                self._ble.gattc_discover_characteristics(
                    self._conn_handle, self._start_handle, self._end_handle
                )
            else:
                print("Failed to find lasertag service.")

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Connected device returned a characteristic.
            conn_handle, def_handle, value_handle, properties, uuid = data
            if conn_handle == self._conn_handle and (uuid == _START_UUID or uuid == _GAME_UUID):
                self._value_handle = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # Characteristic query complete.
            if self._value_handle:
                # We've finished connecting and discovering device, fire the connect callback.
                if self._conn_callback:
                    self._conn_callback()
            else:
                print("Failed to find start characteristic.")

        elif event == _IRQ_GATTC_READ_RESULT:
            # A read completed successfully.
            conn_handle, value_handle, char_data = data
            if conn_handle == self._conn_handle and value_handle == self._value_handle:
                self._update_value(char_data)
                if self._read_callback:
                    self._read_callback(self._value)
                    self._read_callback = None

        elif event == _IRQ_GATTC_READ_DONE:
            # Read completed (no-op).
            conn_handle, value_handle, status = data

        elif event == _IRQ_GATTC_NOTIFY:
            # Check notify message.
            conn_handle, value_handle, notify_data = data
            if conn_handle == self._conn_handle and value_handle == self._value_handle:
                self._update_value(notify_data)
                if self._notify_callback:
                    self._notify_callback(self._value)

    # Returns true if we've successfully connected and discovered characteristics.
    def is_connected(self):
        return self._conn_handle is not None and self._value_handle is not None

    # Find a device advertising the lasertag service.
    def scan(self, callback=None):
        self._addr_type = None
        self._addr = None
        self._scan_callback = callback
        self._ble.gap_scan(2000, 30000, 30000)

    # Connect to the specified device (otherwise use cached address from a scan).
    def connect(self, addr_type=None, addr=None, callback=None):
        self._addr_type = addr_type or self._addr_type
        self._addr = addr or self._addr
        self._conn_callback = callback
        if self._addr_type is None or self._addr is None:
            return False
        self._ble.gap_connect(self._addr_type, self._addr)
        return True

    # Disconnect from current device.
    def disconnect(self):
        if not self._conn_handle:
            return
        self._ble.gap_disconnect(self._conn_handle)
        self._reset()

    # Issues an (asynchronous) read, will invoke callback with data.
    def read(self, callback):
        if not self.is_connected():
            return
        self._read_callback = callback
        self._ble.gattc_read(self._conn_handle, self._value_handle)

    # Sets a callback to be invoked when the device notifies us.
    def on_notify(self, callback):
        self._notify_callback = callback

    def _update_value(self, data):
        #self._value = struct.unpack("<h", data)[0] / 100
        self._value = bytes(data).decode()
        return self._value

    def value(self):
        return self._value


async def demo(fnc_callback_prestart):
    ble = bluetooth.BLE()
    central = BLELasertagCentral(ble)


    found = False

    def on_scan(addr_type, addr, name):
        if addr_type is not None:
            nonlocal found
            print("Found master:", addr_type, addr, name)
            central.connect()
            found = True
        else:
            print("No master found.")

    central.scan(callback=on_scan)
    await uasyncio.sleep(2.5)
    while not found:
        central.scan(callback=on_scan)
        await uasyncio.sleep(2.5)

    # Wait for connection...
    while not central.is_connected():
        await uasyncio.sleep(0.1)
        if not found:
            return

    print("Connected")

    # this callback reassambles split bluetooth messages with start and stop byte "<data>"
    # assembled complete messages end up in prestart_messages (without start and stop byte)
    prestart_messages = []
    prestart_msg_buffer = ""
    def ble_notify_callback(data):
        nonlocal prestart_msg_buffer
        nonlocal prestart_messages
        if data[0] == "<":
            prestart_msg_buffer = data
        elif len(prestart_msg_buffer) != 0:
            prestart_msg_buffer = prestart_msg_buffer + data
        
        if len(prestart_msg_buffer) > 0 and prestart_msg_buffer[0] == "<" and prestart_msg_buffer[-1] == ">":
            prestart_messages.append(prestart_msg_buffer[1:-1])
            prestart_msg_buffer = ""



    # Explicitly issue reads, using "print" as the callback.
    if central.is_connected():
        #central.read(callback=fnc_callback_prestart)
        central.on_notify(callback=ble_notify_callback)

    try:
        while True:
            if len(prestart_messages) > 0:
                mes = prestart_messages.pop()
                fnc_callback_prestart(mes)
            await uasyncio.sleep(1)
    finally:
        central.disconnect()
        print("BLE Disconnected")

    # Alternative to the above, just show the most recently notified value.
    # while central.is_connected():
    #     print(central.value())
    #     time.sleep_ms(2000)

    print("Disconnected")


#if __name__ == "__main__":
    #demo()


c_hiding_time = re.compile(r'([0-9]+)HT_')
c_playing_time = re.compile(r'([0-9]+)PT_')
c_hit_damage = re.compile(r'([0-9]+)HD_')
c_hit_timeout = re.compile(r'([0-9]+)HTO_')
c_shot_ammo = re.compile(r'([0-9]+)SA_')
c_practicing_channel = re.compile(r'([0-9]+)PRC_')
c_playing_channel = re.compile(r'([0-9]+)PLC_')
c_game_id = re.compile(r'([0-9]+)G_')
c_mqtt_during_playing = re.compile(r'(False|True)MQT_')


def parse_prestart_ble_msg(prestart_ble_msg):
    #player_60HT_300PT_30HD_5HTO_0SA_2PRC_4PLC0374G
    parsed = {'hiding_time': int(c_hiding_time.search(prestart_ble_msg).group(1)),
              'playing_time': int(c_playing_time.search(prestart_ble_msg).group(1)),
              'hit_damage': int(c_hit_damage.search(prestart_ble_msg).group(1)),
              'hit_timeout': int(c_hit_timeout.search(prestart_ble_msg).group(1)),
              'shot_ammo': int(c_shot_ammo.search(prestart_ble_msg).group(1)),
              'playing_channel': int(c_playing_channel.search(prestart_ble_msg).group(1)),
              'game_id': c_game_id.search(prestart_ble_msg).group(1),
              'mqtt_during_playing': bool(c_mqtt_during_playing.search(prestart_ble_msg).group(1))}
    return parsed
