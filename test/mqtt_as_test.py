from mqtt_as import MQTTClient, config
import uasyncio as asyncio
import ubinascii
from machine import unique_id

SERVER = '192.168.0.156'  # Change to suit e.g. 'iot.eclipse.org'


# example string flag data: "blueC_100H_AliveS_125T_"
# example string player data: "greenC_00AA11BB22CCI_100H_aliveS_14HI_58SH_125T_"
data_type = "flag"
data_type = "player"
game_id = "2231"
team = "red"
health = "90"
status = "alive"
client_id = ubinascii.hexlify(unique_id()).decode()
hits = 14
shots = 58
remaining_seconds = 125

flag_data = f"{team}C_{health}H_{status}S_{remaining_seconds}T_{game_id}G_"

player_data = f"{team}C_{client_id}I_{health}H_{status}S_{hits}HI_{shots}SH_{remaining_seconds}T_{game_id}G_"



def callback(topic, msg, retained):
    print(topic, msg, retained)

async def conn_han(client):
    await client.subscribe('flag_prestart')

async def main(client):
    await client.connect()
    while True:
        await asyncio.sleep(3)
        # If WiFi is down the following will pause for the duration.

        for client_id in ['e0e2e611d08c','e0e2e611d08b']:
            for team in ['red','green', 'blue']:
                player_data = f"{team}C_{client_id}I_{health}H_{status}S_{hits}HI_{shots}SH_{remaining_seconds}T_{game_id}G_"
                print('publish', player_data)
                await client.publish('player', player_data)

        for team in ['red','green', 'blue']:
            flag_data = f"{team}C_{health}H_{status}S_{remaining_seconds}T_{game_id}G_"
            print('publish', flag_data)
            await client.publish('flag', flag_data)


config['subs_cb'] = callback
config['connect_coro'] = conn_han
config['server'] = SERVER
config['port'] = 1884

# Not needed if you're only using ESP8266
config['ssid'] = 'telenet-FD87E'
config['wifi_pw'] = '556F2kAsxxjT'



MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors