# This example finds and connects to a lasertag master, it enabled notifications and stops on the first one it receives
import uasyncio

import bluetooth
import gc
from binascii import hexlify
from struct import pack, unpack

from ble_advertising import decode_services, decode_name
from message_parser import parse_flag_prestart_msg, parse_player_prestart_msg

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
_IRQ_GATTC_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)


# org.bluetooth.service.lasertag
_LASERTAG_UUID = bluetooth.UUID(0x936b)
# org.bluetooth.characteristic.start
_PRESTART_FLAG_UUID = bluetooth.UUID(0xc20a)
_PRESTART_PLAYER_UUID = bluetooth.UUID(0xc20b)
_NEXT_ROUND_UUID = bluetooth.UUID(0xc20c)
# Standard UUID Characteristic
_SUC_UUID = bluetooth.UUID(0x2803)
# CCCD Client Characteristic Configuration Descriptor
_CCCD_UUID = bluetooth.UUID(0x2902)

class BLELasertagCharacteristic:
    """
    Holds the necessary handles
    """
    def __init__(self, uuid) -> None:
        self.uuid = uuid
        self._reset()

    def _reset(self):
        self._def_handle = None
        self._value_handle = None
        self._cccd_handle = None

        # Cached value (if we have one)
        self._value = None

        # Callbacks for completion of various operations.
        # These reset back to None after being invoked.
        self._read_callback = None
        self._write_callback = None
        self._read_cccd_callback = None
        self._write_cccd_callback = None

        # Persistent callback for when new data is notified from the device.
        self._notify_callback = None


    @property
    def def_handle(self):
        return self._def_handle

    @def_handle.setter
    def def_handle(self, value):
        self._def_handle = value

    @property
    def value_handle(self):
        return self._value_handle

    @value_handle.setter
    def value_handle(self, value):
        self._value_handle = value

    @property
    def cccd_handle(self):
        return self._cccd_handle

    @cccd_handle.setter
    def cccd_handle(self, value):
        self._cccd_handle = value

    @property
    def value(self):
        return self._value

    # to be called from the irq
    @value.setter
    def value(self, value):
        self._value = bytes(value).decode()


    @property
    def read_callback(self):
        return self._read_callback

    @read_callback.setter
    def read_callback(self, value):
        self._read_callback = value

    @property
    def write_callback(self):
        return self._write_callback

    @write_callback.setter
    def write_callback(self, value):
        self._write_callback = value

    @property
    def read_cccd_callback(self):
        return self._read_cccd_callback

    @read_cccd_callback.setter
    def read_cccd_callback(self, value):
        self._read_cccd_callback = value

    @property
    def write_cccd_callback(self):
        return self._write_cccd_callback

    @write_cccd_callback.setter
    def write_cccd_callback(self, value):
        self._write_cccd_callback = value


    @property
    def notify_callback(self):
        return self._notify_callback

    @notify_callback.setter
    def notify_callback(self, value):
        self._notify_callback = value


class BLELasertagCentral:
    def __init__(self, ble, characteristic_uuid):
        self._ble = ble
        self._ble.active(True)
        ble.config(rxbuf=1551)  # 3 x 517 (517 = max mtu)
        self._ble.irq(self._irq)
        self._characteristic_uuid = characteristic_uuid

        self._reset()
        self._disconn_callback = None

    def _reset(self):
        # Cached name and address from a successful scan.
        self._name = None
        self._addr_type = None
        self._addr = None
        self._connected = False

        # Callbacks for completion of various operations.
        # These reset back to None after being invoked.
        self._scan_callback = None
        self._conn_callback = None
        self._conn_failed_callback = None
        # self._disconn_callback = None  # special case, we reset this manually, otherwise the callback is lost

        # Connected device.
        self._conn_handle = None
        self._lasertag_start_handle = None
        self._lasertag_end_handle = None
        self._descriptors = []
        self._characteristics = {
            self._characteristic_uuid: BLELasertagCharacteristic(self._characteristic_uuid)
        }

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND) and _LASERTAG_UUID in decode_services(adv_data):
                print("event _IRQ_SCAN_RESULT", decode_name(adv_data), rssi, decode_services(adv_data))
                # Found a potential device, remember it and stop scanning.
                self._addr_type = addr_type
                self._addr = bytes(addr)  # Note: addr buffer is owned by caller so need to copy it.
                self._name = decode_name(adv_data) or "?"
                self._ble.gap_scan(None)

        elif event == _IRQ_SCAN_DONE:
            print("event _IRQ_SCAN_DONE")
            if self._scan_callback is not None:
                if self._addr is not None:
                    # Found a device during the scan (and the scan was explicitly stopped).
                    self._scan_callback(self._addr_type, self._addr, self._name)
                else:
                    # Scan timed out.
                    self._scan_callback(None, None, None)
                self._scan_callback = None

        elif event == _IRQ_PERIPHERAL_CONNECT:
            # Connect successful.
            conn_handle, addr_type, addr = data
            print("event _IRQ_PERIPHERAL_CONNECT conn_handle", conn_handle, "addr_type", addr_type, "addr", addr)
            if addr_type == self._addr_type and addr == self._addr:
                self._conn_handle = conn_handle
                self._ble.config(mtu=517)
                self._ble.gattc_exchange_mtu(self._conn_handle)
                self._ble.gattc_discover_services(self._conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Disconnect (either initiated by us or the remote end).
            conn_handle, addr_type, addr = data
            print("event: _IRQ_PERIPHERAL_DISCONNECT self._conn_handle", self._conn_handle, "conn_handle", conn_handle, self._disconn_callback)
            if self._disconn_callback is not None:
                self._disconn_callback()
                self._disconn_callback = None
            if self._conn_handle is not None and conn_handle == self._conn_handle:
                # If it was initiated by us, it'll already be reset.
                self._reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Connected device returned a service.
            conn_handle, start_handle, end_handle, uuid = data
            print("event _IRQ_GATTC_SERVICE_RESULT conn_handle", conn_handle, "start_handle", start_handle, "end_handle", end_handle, "uuid", uuid)
            if conn_handle == self._conn_handle and uuid == _LASERTAG_UUID:
                self._lasertag_start_handle, self._lasertag_end_handle = start_handle, end_handle

        elif event == _IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            print("event _IRQ_GATTC_SERVICE_DONE conn_handle", conn_handle, "status", status)
            # Service query complete.
            if status == 0 and self._conn_handle == conn_handle and self._lasertag_start_handle is not None and self._lasertag_end_handle is not None:
                self._ble.gattc_discover_characteristics(
                    self._conn_handle, self._lasertag_start_handle, self._lasertag_end_handle
                )
            else:
                print("Failed to find lasertag service.")
                try:
                    self._ble.gap_disconnect(self._conn_handle)
                except Exception as e:
                    print(e)
                if self._conn_failed_callback is not None:
                    self._conn_failed_callback()
                    self._conn_failed_callback = None

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Connected device returned a characteristic.
            conn_handle, def_handle, value_handle, properties, uuid = data
            print("event _IRQ_GATTC_CHARACTERISTIC_RESULT def_handle", def_handle, "value_handle", value_handle, "properties", properties, "uuid", uuid)
            if conn_handle == self._conn_handle:
                if uuid in self._characteristics:
                    self._characteristics[uuid].def_handle = def_handle
                    self._characteristics[uuid].value_handle = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            conn_handle, status = data
            # Characteristic query complete.
            print("event _IRQ_GATTC_CHARACTERISTIC_DONE self._lasertag_start_handle", self._lasertag_start_handle,
                  "self._lasertag end_handle", self._lasertag_end_handle)
            if status == 0 and self._conn_handle == conn_handle:
                self._ble.gattc_discover_descriptors(
                    self._conn_handle, self._lasertag_start_handle, self._lasertag_end_handle
                )
            else:
                print("Failed to find lasertag characteristic.")
                try:
                    self._ble.gap_disconnect(self._conn_handle)
                except Exception as e:
                    print(e)
                if self._conn_failed_callback is not None:
                    self._conn_failed_callback()
                    self._conn_failed_callback = None

        elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
            conn_handle, dsc_handle, uuid = data
            print("event _IRQ_GATTC_DESCRIPTOR_RESULT conn_handle", conn_handle, "dsc_handle", dsc_handle, "uuid", uuid)
            if conn_handle == self._conn_handle:
                self._descriptors.append((dsc_handle, bluetooth.UUID(uuid)))

        elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
            print("event _IRQ_GATTC_DESCRIPTOR_DONE")
            conn_handle, status = data

            def failed_connection():
                print("Failed to find lasertag descriptor.")
                try:
                    self._ble.gap_disconnect(self._conn_handle)
                except Exception as e:
                    print(e)
                if self._conn_failed_callback is not None:
                    self._conn_failed_callback()
                    self._conn_failed_callback = None

            if status == 0 and self._conn_handle == conn_handle:
                # loop over the found descriptors and try to find the corresponding cccd for each characteristic
                # order of appearance _SUC_UUID, defined_uuid, _CCCD_UUID
                current_characteristic = None
                for dsc_handle, uuid in self._descriptors:
                    if uuid == _SUC_UUID:
                        if current_characteristic is None:
                            for characteristic in self._characteristics.values():
                                if dsc_handle == characteristic.def_handle:
                                    current_characteristic = characteristic
                                    break
                    elif current_characteristic is not None and uuid == current_characteristic.uuid:
                        if dsc_handle != current_characteristic.value_handle:
                            print("discovered value handles do not match", dsc_handle, current_characteristic.value_handle)
                    elif current_characteristic is not None and uuid == _CCCD_UUID:
                        current_characteristic.cccd_handle = dsc_handle
                        # this was the last descriptor, reset for next in loop
                        current_characteristic = None

                for characteristic in self._characteristics.values():
                    if characteristic.def_handle is None or characteristic.value_handle is None or characteristic.cccd_handle is None:
                        failed_connection()

                # We've finished connecting and discovering device, fire the connect callback.
                if self._conn_callback is not None:
                    self._conn_callback()
                    self._conn_callback = None
                self._connected = True
            else:
                failed_connection()

        elif event == _IRQ_GATTC_READ_RESULT:
            # A read completed successfully.
            conn_handle, value_handle, char_data = data
            print("event _IRQ_GATTC_READ_RESULT conn_handle", conn_handle, "value_handle", value_handle, "char_data", bytes(char_data))

            if conn_handle == self._conn_handle:
                for characteristic in self._characteristics.values():
                    if value_handle == characteristic.value_handle:
                        characteristic.value = char_data
                        if characteristic.read_callback is not None:
                            characteristic.read_callback(characteristic.value)
                            characteristic.read_callback = None
                        break
                    elif value_handle == characteristic.cccd_handle:
                        if characteristic.read_callback is not None:
                            characteristic.read_callback(bytes(char_data).decode())
                            characteristic.read_callback = None
                        break

        elif event == _IRQ_GATTC_READ_DONE:
            print("event _IRQ_GATTC_READ_DONE")
            # Read completed (no-op).
            conn_handle, value_handle, status = data

        elif event == _IRQ_GATTC_WRITE_DONE:
            print("event _IRQ_GATTC_WRITE_DONE")
            # Write completed (no-op).
            conn_handle, value_handle, status = data

        elif event == _IRQ_GATTC_NOTIFY:
            # Check notify message.
            conn_handle, value_handle, notify_data = data
            print("event _IRQ_GATTC_NOTIFY notify_data", bytes(notify_data).decode())
            if conn_handle == self._conn_handle:
                for characteristic in self._characteristics.values():
                    if value_handle == characteristic.value_handle:
                        characteristic.value = notify_data
                        if characteristic.notify_callback is not None:
                            characteristic.notify_callback(characteristic.value)
                        break

        elif event == _IRQ_MTU_EXCHANGED:
            conn_handle, mtu = data
            print("event _IRQ_MTU_EXCHANGED mtu", mtu)

    # Returns true if we've successfully connected and discovered characteristics and descriptors.
    def is_connected(self):
        return self._conn_handle is not None and self._connected

    # Find a device advertising the lasertag service.
    def scan(self, callback=None):
        self._addr_type = None
        self._addr = None
        self._scan_callback = callback
        self._ble.gap_scan(2000, 30000, 30000)

    # Connect to the specified device (otherwise use cached address from a scan).
    def connect(self, addr_type=None, addr=None, callback=None, failed_callback=None, disconnect_callback=None):
        self._addr_type = addr_type or self._addr_type
        self._addr = addr or self._addr
        self._conn_callback = callback
        self._conn_failed_callback = failed_callback
        self._disconn_callback = disconnect_callback
        if self._addr_type is None or self._addr is None:
            return False
        self._ble.gap_connect(self._addr_type, self._addr)
        return True

    # Disconnect from current device.
    def disconnect(self, callback):
        if self._conn_handle is None:
            return
        self._disconn_callback = callback
        for characteristic in self._characteristics.values():
            characteristic.notify_callback = None
        self._ble.gap_disconnect(self._conn_handle)
        self._reset()

    # Issues an (asynchronous) read, will invoke callback with data.
    def read(self, uuid, callback):
        if not self.is_connected():
            return
        self._characteristics[uuid].read_callback = callback
        self._ble.gattc_read(self._conn_handle, self._characteristics[uuid].value_handle)

    def write(self, uuid, data, callback):
        if callback is None:
            mode = 0  # 0 no write confirmation, 1 with write confirmation
        else:
            self._characteristics[uuid].write_callback = callback
            mode = 1
        self._ble.gattc_write(self._conn_handle, self._characteristics[uuid].value_handle, data, mode)

    # first byte of cccd should be 1, first we read it, then write if needed
    def _enable_notifications(self, uuid):

        def cccd_read_callback(value):
            orig = unpack('<bb', value)
            if orig[0] != 1:
                cccd_value = pack('<bb', 1, 0)
                self._ble.gattc_write(self._conn_handle, self._characteristics[uuid].cccd_handle, cccd_value, 0)

        self._characteristics[uuid].read_callback = cccd_read_callback
        self._ble.gattc_read(self._conn_handle, self._characteristics[uuid].cccd_handle)

    # Sets a callback to be invoked when the device notifies us.
    def on_notify(self, callback):
        self._enable_notifications(self._characteristic_uuid)
        self._characteristics[self._characteristic_uuid].notify_callback = callback


BLE_LISTEN_TYPE_PRESTART_FLAG = const("BLE_LISTEN_TYPE_PRESTART_FLAG")
BLE_LISTEN_TYPE_PRESTART_PLAYER = const("BLE_LISTEN_TYPE_PRESTART_PLAYER")
BLE_LISTEN_TYPE_NEXT_ROUND = const("BLE_LISTEN_TYPE_NEXT_ROUND")


async def ble_listener(listen_type, fnc_callback_ble_notify):
    ble = bluetooth.BLE()

    if listen_type == BLE_LISTEN_TYPE_PRESTART_FLAG:
        central = BLELasertagCentral(ble, _PRESTART_FLAG_UUID)
    elif listen_type == BLE_LISTEN_TYPE_PRESTART_PLAYER:
        central = BLELasertagCentral(ble, _PRESTART_PLAYER_UUID)
    elif listen_type == BLE_LISTEN_TYPE_NEXT_ROUND:
        central = BLELasertagCentral(ble, _NEXT_ROUND_UUID)
    else:
        raise Exception("unknown listen_type:" + listen_type)

    BLE_START_SCANNING = const("BLE_START_SCANNING")
    BLE_SCANNING = const("BLE_SCANNING")
    BLE_MASTER_FOUND = const("BLE_MASTER_FOUND")
    BLE_CONNECTING = const("BLE_CONNECTING")
    BLE_CONNECTED = const("BLE_CONNECTED")
    BLE_LISTENING = const("BLE_LISTENING")
    BLE_MESSAGE_RECEIVED = const("BLE_MESSAGE_RECEIVED")
    BLE_INITIATE_DISCONNECT = const("BLE_INITIATE_DISCONNECT")
    BLE_DISCONNECTING = const("BLE_DISCONNECTING")
    BLE_END = const("BLE_END")

    current_state = BLE_START_SCANNING

    def on_scan(addr_type, addr, name):
        if addr_type is not None:
            nonlocal current_state
            a = hexlify(addr, '-').decode()
            print("Found master:", a, name)
            current_state = BLE_MASTER_FOUND
        else:
            print("No master found.")
            current_state = BLE_START_SCANNING

    def on_connect():
        nonlocal current_state
        current_state = BLE_CONNECTED

    def on_failed_connect():
        nonlocal current_state
        current_state = BLE_START_SCANNING

    def on_disconnect():
        nonlocal current_state
        print("disconnected, BLE_START_SCANNING")
        current_state = BLE_START_SCANNING

    def on_final_disconnect():
        nonlocal current_state
        print("disconnected, ending loop")
        current_state = BLE_END

    ble_notify_messages = []
    def ble_notify_callback(data):
        nonlocal current_state
        nonlocal ble_notify_messages
        ble_notify_messages.append(data)
        current_state = BLE_MESSAGE_RECEIVED

    try:
        while True:
            if current_state == BLE_START_SCANNING:
                print("BLE_START_SCANNING")
                central.scan(callback=on_scan)
                current_state = BLE_SCANNING

            elif current_state == BLE_SCANNING:
                await uasyncio.sleep(0.1)

            elif current_state == BLE_MASTER_FOUND:
                #await uasyncio.sleep(0.5)
                central.connect(callback=on_connect, failed_callback=on_failed_connect, disconnect_callback=on_disconnect)
                #await uasyncio.sleep(0.1)
                current_state = BLE_CONNECTING

            elif current_state == BLE_CONNECTING:
                await uasyncio.sleep(0.1)

            elif current_state == BLE_CONNECTED:
                print("BLE_CONNECTED")
                central.on_notify(callback=ble_notify_callback)
                current_state = BLE_LISTENING

            elif current_state == BLE_LISTENING:
                await uasyncio.sleep(0.1)
                if not central.is_connected():
                    current_state = BLE_START_SCANNING

            elif current_state == BLE_MESSAGE_RECEIVED:
                if not central.is_connected():
                    current_state = BLE_START_SCANNING

                if len(ble_notify_messages) > 0:
                    mes = ble_notify_messages.pop()
                    print("got notified message", mes)
                    if listen_type == BLE_LISTEN_TYPE_PRESTART_FLAG:
                        parsed_mes = parse_flag_prestart_msg(mes)
                    elif listen_type == BLE_LISTEN_TYPE_PRESTART_PLAYER:
                        parsed_mes = parse_player_prestart_msg(mes)
                    elif listen_type == BLE_LISTEN_TYPE_NEXT_ROUND:
                        parsed_mes = mes
                    else:
                        raise Exception("unknown listen_type:" + listen_type)

                    should_we_stop = fnc_callback_ble_notify(parsed_mes)
                    if should_we_stop:
                        current_state = BLE_INITIATE_DISCONNECT
                else:
                    await uasyncio.sleep(0.5)

            elif current_state == BLE_INITIATE_DISCONNECT:
                await uasyncio.sleep(0.5)  # at least 10 x connection_timeout (default connection_timeout is between 30000us and 50000us)
                central.disconnect(on_final_disconnect)
                current_state = BLE_DISCONNECTING

            elif current_state == BLE_DISCONNECTING:
                await uasyncio.sleep(0.1)

            elif current_state == BLE_END:
                break

    finally:
        if central.is_connected():
            central.disconnect(None)
            print("BLE Disconnected")
            gc.collect()

