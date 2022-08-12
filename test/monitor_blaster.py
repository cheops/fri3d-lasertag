import uasyncio
import blaster

my_team = blaster.Team.rex

blaster.blaster.set_team(my_team)


async def monitor_blaster():
    while True:
        await uasyncio.sleep(0.5)
        data_packet = blaster.blaster.get_blaster_shot()
        #print(data_packet)

        if data_packet is not None \
                and data_packet.command == blaster.Command.shoot \
                and data_packet.trigger == False \
                and data_packet.team_str != my_team:
            # incoming enemy fire
            print('got_hit', data_packet)

uasyncio.run(monitor_blaster())



