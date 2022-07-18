import uasyncio
import blaster
import teams


async def monitor_blaster(my_team, got_hit_fnc):
    while True:
        uasyncio.sleep(100)
        data_packet = blaster.blaster.get_blaster_shot()
        if data_packet.team_str() == teams.team_blaster[my_team]:
            dead = got_hit_fnc()
            if dead:
                break
