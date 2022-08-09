# docs https://mpython.readthedocs.io/en/master/library/mPython/umqtt.simple.html
# https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/README.md

import time
import network
import ubinascii

from machine import unique_id

import umqtt.simple

FRI3D_WIFI_SSID = 'fri3d-badge'
FRI3D_WIFI_PASSWORD = 'fri3dcamp'
# example string flag data: "blueC_100H_AliveS_125T_"
# example string player data: "greenC_00AA11BB22CCI_100H_aliveS_14HI_58SH_125T_"
data_type = "flag"
data_type = "player"
game_id = "0012"
team = "red"
health = "100"
status = "alive"
client_id = ubinascii.hexlify(unique_id()).decode('ascii')
hits = 14
shots = 58
remaining_seconds = 125

flag_data = f"{game_id}G_{team}C_{health}H_{status}S_{remaining_seconds}T_"

player_data = f"{team}C_{client_id}I_{health}H_{status}S_{hits}HI_{shots}SH_{remaining_seconds}T_{game_id}G_"


def _connect_wifi():
    station = network.WLAN(network.STA_IF)
    if not station.isconnected():

        station.active(True)
        station.connect(FRI3D_WIFI_SSID, FRI3D_WIFI_PASSWORD)

    while not station.isconnected():
        pass

    print('wifi connection successful')
    print(station.ifconfig())


def mqtt_subscribe_callback(topic, msg):
    print('mqtt callback')
    print(topic, msg)


def _mqtt_client():
    mqtt_server = '192.168.0.156'
    port = 1884  # default 1883
    user = 'jan'
    password = 'stappers'
    client_id = ubinascii.hexlify(unique_id())
    client = umqtt.simple.MQTTClient(client_id, mqtt_server, port=port, user=user, password=password, keepalive=60)

    client.set_callback(mqtt_subscribe_callback)
    client.connect()
    subscribe_topic = 'flag_prestart'
    client.subscribe(subscribe_topic)
    subscribe_topic = 'player_prestart'
    client.subscribe(subscribe_topic)
    subscribe_topic = 'device_stop'
    client.subscribe(subscribe_topic)

    return client

def test():
    _connect_wifi()

    client = _mqtt_client()

    while True:
        client.publish('player', player_data)
        client.check_msg()

        print('.')
        time.sleep(5)


test()
