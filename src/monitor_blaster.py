import uasyncio
from hardware import blaster
import teams
from blaster import Command


async def monitor_blaster(my_team, got_hit_fnc):
    while True:
        await uasyncio.sleep(0.1)
        data_packet = blaster.blaster.get_blaster_shot()
        
        if data_packet is not None \
                and data_packet.command() == Command.shoot \
                and data_packet.trigger() == 1 \
                and data_packet.team_str() != teams.team_blaster[my_team]:
            # incoming enemy fire
            dead = got_hit_fnc()
            if dead:
                break
