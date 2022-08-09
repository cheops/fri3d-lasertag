from mqtt_as import MQTTClient, config
import uasyncio as asyncio
import ubinascii
from machine import unique_id
import re

SERVER = '192.168.0.156'  # Change to suit e.g. 'iot.eclipse.org'
PORT = 1883
FRI3D_WIFI_SSID = 'fri3d-badge'
FRI3D_WIFI_PASSWORD = 'fri3dcamp'

client_id = ubinascii.hexlify(unique_id()).decode()
subscription_callbacks = {}
subscription_topics = ['flag_prestart', 'player_prestart', 'device_stop']


def _callback(topic, msg, retained):
    print((topic, msg, retained))
    if topic in subscription_callbacks:
        subscription_callbacks[topic](msg)


async def _conn_han(the_client):
    for topic in subscription_topics:
        await the_client.subscribe(topic)


async def publish_mqtt_flag(team, game_id, fnc_get_health, fnc_get_remaining_seconds):
    try:
        await client.connect()
        while True:
            health = fnc_get_health()
            status = "alive" if health > 0 else "dead"
            remaining_seconds = fnc_get_remaining_seconds()
            flag_data = f"{team}C_{health}H_{status}S_{remaining_seconds}T_{game_id}G_"

            await client.publish('flag', flag_data)
            await asyncio.sleep(5)
    finally:
        client.close()


async def publish_mqtt_player(team, game_id, fnc_get_health, fnc_get_hits, fnc_get_shots, fnc_get_remaining_seconds):
    try:
        await client.connect()
        while True:
            health = fnc_get_health()
            status = "alive" if health > 0 else "dead"
            remaining_seconds = fnc_get_remaining_seconds()
            hits = fnc_get_hits()
            shots = fnc_get_shots()
            player_data = f"{team}C_{client_id}I_{health}H_{status}S_{hits}HI_{shots}SH_{remaining_seconds}T_{game_id}G_"

            await client.publish('player', player_data)
            await asyncio.sleep(5)
    finally:
        client.close()


def subscribe_flag_prestart(fnc_callback_prestart):
    subscription_callbacks['flag_prestart'] = fnc_callback_prestart


def unsubscribe_flag_prestart():
    del subscription_callbacks['flag_prestart']


def subscribe_player_prestart(fnc_callback_prestart):
    subscription_callbacks['player_prestart'] = fnc_callback_prestart


def unsubscribe_player_prestart():
    del subscription_callbacks['player_prestart']


def subscribe_device_stop(fnc_callback_stop):
    subscription_callbacks['device_stop'] = fnc_callback_stop


def unsubscribe_device_stop():
    del subscription_callbacks['device_stop']


config['subs_cb'] = _callback
config['connect_coro'] = _conn_han
config['server'] = SERVER
config['port'] = PORT

# Not needed if you're only using ESP8266
config['ssid'] = FRI3D_WIFI_SSID
config['wifi_pw'] = FRI3D_WIFI_PASSWORD


MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)


def close_client():
    client.close()


c_hiding_time = re.compile(r'(?P<hiding_time>[0-9]+)HT_')
c_playing_time = re.compile(r'(?P<playing_time>[0-9]+)PT_')
c_hit_damage = re.compile(r'(?P<hit_damage>[0-9]+)HD_')
c_hit_timeout = re.compile(r'(?P<hit_timeout>[0-9]+)HTO_')
c_shot_ammo = re.compile(r'(?P<shot_ammo>[0-9]+)SA_')
c_practicing_channel = re.compile(r'(?P<practicing_channel>[0-9]+)PRC_')
c_playing_channel = re.compile(r'(?P<playing_channel>[0-9]+)PLC_')
c_game_id = re.compile(r'(?P<game_id>[0-9]+)G_')


def get_hiding_time(player_prestart):
    m = c_hiding_time.search(player_prestart)
    return m.group('hiding_time')
def get_playing_time(player_prestart):
    m = c_playing_time.search(player_prestart)
    return m.group('playing_time')
def get_hit_damage(player_prestart):
    m = c_hit_damage.search(player_prestart)
    return m.group('hit_damage')
def get_hit_timeout(player_prestart):
    m = c_hit_timeout.search(player_prestart)
    return m.group('hit_timeout')
def get_shot_ammo(player_prestart):
    m = c_shot_ammo.search(player_prestart)
    return m.group('shot_ammo')
def get_practicing_channel(player_prestart):
    m = c_practicing_channel.search(player_prestart)
    return m.group('practicing_channel')
def get_playing_channel(player_prestart):
    m = c_playing_channel.search(player_prestart)
    return m.group('playing_channel')
def get_game_id(player_prestart):
    m = c_game_id.search(player_prestart)
    return m.group('game_id')
