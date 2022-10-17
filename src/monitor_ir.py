import uasyncio
from hardware import blaster
from teams import team_blaster
from blaster import Command


def clear_blaster_buffer():
    while blaster.blaster.get_blaster_shot() is not None:
        pass


async def monitor_blaster(my_team, got_hit_fnc, shot_fnc):
    try:
        while True:
            await uasyncio.sleep(0.5)
            data_packet = blaster.blaster.get_blaster_shot()

            if data_packet is not None \
                    and data_packet.command == Command.shoot \
                    and data_packet.trigger is False \
                    and data_packet.team != team_blaster[my_team]:
                # incoming enemy fire
                dead = got_hit_fnc()
                if dead:
                    break

            if data_packet is not None \
                    and data_packet.command == Command.shoot \
                    and data_packet.trigger is True \
                    and data_packet.team == team_blaster[my_team]:
                # we shoot
                await shot_fnc()
    except uasyncio.CancelledError:
        pass

def clear_badge_buffer():
    while get_badge_shot(-1) is not None:
        pass


async def monitor_badge(my_team, channel, got_hit_fnc):
    while True:
        await uasyncio.sleep(0.5)
        data_packet = get_badge_shot(channel)

        if data_packet is not None \
                and data_packet.command == Command.shoot \
                and data_packet.trigger is True \
                and data_packet.team != team_blaster[my_team]:
            # incoming enemy fire
            dead = got_hit_fnc()
            if dead:
                break


def get_badge_shot(channel):
    p = blaster.blaster._ir_link.read_packet()
    if not p:
        return
    if p.command not in [Command.heal, Command.shoot]:
        return
    if channel != -1 and not p.parameter == channel:
        return
    return p
