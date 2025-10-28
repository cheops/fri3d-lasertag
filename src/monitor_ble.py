# This example listens for lastertag master broadcast messages and stops on the first one received
import time

import uasyncio

import bluetooth
#from binascii import hexlify
from micropython import const
import gc

from ble_advertising import decode_man_spec_data

_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)
_ADV_SCAN_RSP = const(0x04)

_OUR_COMPANY_ID = const(b'\xff\xff')
_OUR_BL_ADDR = const(b'\xde\xad\xbe\xef\xca\xfe')

PRESTART_TYPE = const(0)
NEXT_ROUND_TYPE = const(1)


class BLELasertagCentral:
    def __init__(self, ble, mes_type):
        self._ble = ble
        self._ble.irq(self._irq)
        self._man_spec_data = None
        self._scan_callback = None

        self._reset()
        self._listen_mes_type = mes_type

    def _reset(self):
        # Cached manufacturer specific data from a successful scan.
        self._man_spec_data = None

    def _irq(self, event, data):

        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            #print("addr_type=", addr_type, ", addr=", bytes(addr), ", adv_type=", adv_type, ", rssi=", rssi, "adv_data=", bytes(adv_data))
            if adv_type == _ADV_NONCONN_IND and addr == _OUR_BL_ADDR:
                c_id, man_spec_data = decode_man_spec_data(adv_data)
                if _OUR_COMPANY_ID == c_id and man_spec_data[0] == self._listen_mes_type:
                    # Found the required broadcast message, remember it and stop scanning.
                    self._man_spec_data = bytes(man_spec_data)
                    self._ble.gap_scan(None)  # stop scanning

        elif event == _IRQ_SCAN_DONE:
            #print("event _IRQ_SCAN_DONE")
            if self._scan_callback is not None:
                if self._man_spec_data is not None:
                    # Found a device during the scan (and the scan was explicitly stopped).
                    self._scan_callback(self._man_spec_data)
                else:
                    # Scan timed out.
                    self._scan_callback(None)
                self._scan_callback = None

    # Find a device advertising the lasertag service.
    def scan(self, callback=None):
        self._reset()
        self._scan_callback = callback
        self._ble.active(True)
        self._ble.gap_scan(2_000, 120_000, 30_000, False)  # scan during 2 seconds, every 120ms for 30ms


async def ble_listener(listen_type, fnc_callback_ble_notify):
    ble = bluetooth.BLE()
    ble.config(rxbuf=370)  # 10 broadcasts packets

    central = BLELasertagCentral(ble, listen_type)

    BLE_START_SCANNING = const("BLE_START_SCANNING")
    BLE_RESTART_SCANNING = const("BLE_RESTART_SCANNING")
    BLE_SCANNING = const("BLE_SCANNING")
    BLE_MESSAGE_RECEIVED = const("BLE_MESSAGE_RECEIVED")
    BLE_END = const("BLE_END")

    current_state = BLE_START_SCANNING
    ble_msg = None

    def on_scan(man_spec_data):
        nonlocal current_state
        nonlocal ble_msg
        if man_spec_data is not None:
            ble_msg = man_spec_data
            current_state = BLE_MESSAGE_RECEIVED
        else:
            #print("No master found.")
            current_state = BLE_RESTART_SCANNING

    try:
        while True:
            if current_state == BLE_START_SCANNING:
                #print("BLE_START_SCANNING")
                central.scan(callback=on_scan)
                current_state = BLE_SCANNING

            elif current_state == BLE_RESTART_SCANNING:
                # sleep a bit to go easy on ble
                await uasyncio.sleep(1)
                current_state = BLE_START_SCANNING

            elif current_state == BLE_SCANNING:
                await uasyncio.sleep(0.1)

            elif current_state == BLE_MESSAGE_RECEIVED:
                if ble_msg is not None:
                    print("ble got broadcast message", ble_msg)

                    fnc_callback_ble_notify(ble_msg)
                    ble_msg = None
                    current_state = BLE_END
                else:
                    # we think we got a message, but there is no message
                    current_state = BLE_START_SCANNING
                    await uasyncio.sleep(0.5)

            elif current_state == BLE_END:
                ble.active(False)
                break

    except uasyncio.CancelledError:
        pass
    finally:
        try:
            ble.gap_scan(None)
        except:
            pass 
        ble.active(False)


