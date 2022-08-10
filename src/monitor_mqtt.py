import gc

from mqtt_as import MQTTClient, config
import uasyncio
import ubinascii
from machine import unique_id
import re

from teams import team_mqtt

MQTTClient.DEBUG = True  # Optional: print diagnostic messages

MQTT_SERVER = '192.168.0.140'  # Change to suit e.g. 'iot.eclipse.org'
MQTT_PORT = 1883
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
        my_client = await get_client()
        while True:
            health = fnc_get_health()
            status = "alive" if health > 0 else "dead"
            remaining_seconds = fnc_get_remaining_seconds()
            flag_data = f"{team_mqtt[team]}C_{health}H_{status}S_{remaining_seconds}T_{game_id}G_"

            await my_client.publish('flag', flag_data)
            await uasyncio.sleep(5)
    finally:
        close_client()


async def publish_mqtt_player(team, game_id, fnc_get_health, fnc_get_hits, fnc_get_shots, fnc_get_remaining_seconds):
    try:
        my_client = await get_client()
        while True:
            health = fnc_get_health()
            status = "alive" if health > 0 else "dead"
            remaining_seconds = fnc_get_remaining_seconds()
            hits = fnc_get_hits()
            shots = fnc_get_shots()
            player_data = f"{team_mqtt[team]}C_{client_id}I_{health}H_{status}S_{hits}HI_{shots}SH_{remaining_seconds}T_{game_id}G_"

            await my_client.publish('player', player_data)
            await uasyncio.sleep(5)
    finally:
        close_client()


async def subscribe_flag_prestart(fnc_callback_prestart):
    await get_client()
    subscription_callbacks['flag_prestart'] = fnc_callback_prestart
    try:
        while True:
            await uasyncio.sleep(1)
    finally:
        del subscription_callbacks['flag_prestart']
        close_client()


def subscribe_player_prestart(fnc_callback_prestart):
    await get_client()
    subscription_callbacks['player_prestart'] = fnc_callback_prestart
    try:
        while True:
            await uasyncio.sleep(1)
    finally:
        del subscription_callbacks['player_prestart']
        close_client()


def subscribe_device_stop(fnc_callback_stop):
    await get_client()
    subscription_callbacks['device_stop'] = fnc_callback_stop
    try:
        while True:
            await uasyncio.sleep(1)
    finally:
        del subscription_callbacks['device_stop']
        close_client()


config['subs_cb'] = _callback
config['connect_coro'] = _conn_han
config['server'] = MQTT_SERVER
config['port'] = MQTT_PORT
config['ssid'] = FRI3D_WIFI_SSID
config['wifi_pw'] = FRI3D_WIFI_PASSWORD

client = None
client_ref_count = 0


async def get_client():
    global client
    global client_ref_count
    if client is None:
        client = MQTTClient(config)
        await client.connect()
    client_ref_count += 1
    return client


def close_client():
    global client
    global client_ref_count
    client_ref_count -= 1
    if client_ref_count == 0 and client is not None:
        client.close()
        client = None
        gc.collect()


c_hiding_time = re.compile(r'([0-9]+)HT_')
c_playing_time = re.compile(r'([0-9]+)PT_')
c_hit_damage = re.compile(r'([0-9]+)HD_')
c_hit_timeout = re.compile(r'([0-9]+)HTO_')
c_shot_ammo = re.compile(r'([0-9]+)SA_')
c_practicing_channel = re.compile(r'([0-9]+)PRC_')
c_playing_channel = re.compile(r'([0-9]+)PLC_')
c_game_id = re.compile(r'([0-9]+)G_')


def parse_player_prestart_mqtt_msg(player_prestart):
    #player_60HT_300PT_30HD_5HTO_0SA_2PRC_4PLC0374G
    parsed = {'hiding_time': c_hiding_time.search(player_prestart).group(1),
              'playing_time': c_playing_time.search(player_prestart).group(1),
              'hit_damage': c_hit_damage.search(player_prestart).group(1),
              'hit_timeout': c_hit_timeout.search(player_prestart).group(1),
              'shot_ammo': c_shot_ammo.search(player_prestart).group(1),
              'playing_channel': c_playing_channel.search(player_prestart).group(1),
              'game_id': c_game_id.search(player_prestart).group(1)}
    return parsed


def parse_flag_prestart_mqtt_msg(player_prestart):
    #flag_60HT_300PT_30HD_5HTO_2PRC_4PLC0374G
    parsed = {'hiding_time': c_hiding_time.search(player_prestart).group(1),
              'playing_time': c_playing_time.search(player_prestart).group(1),
              'hit_damage': c_hit_damage.search(player_prestart).group(1),
              'hit_timeout': c_hit_timeout.search(player_prestart).group(1),
              'playing_channel': c_playing_channel.search(player_prestart).group(1),
              'game_id': c_game_id.search(player_prestart).group(1)}
    return parsed
