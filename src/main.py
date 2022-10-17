import uasyncio

from mvp import states_mvp, transitions_mvp, BOOTING
from profiles_mvp import player_buzz_profile
from statemachine import StateMachine
from time import sleep
from effects import effect_star_wars, effect_clean

effect_star_wars()
sleep(0.5)
effect_clean()

# uasyncio is complicated and not easy and not straight forward
# documentation
#     https://github.com/peterhinch/micropython-async/blob/master/v3/README.md
#     https://docs.micropython.org/en/latest/library/uasyncio.html
#

# _thread documentation
# https://www.youtube.com/watch?v=aDXgX0rGVDY
# https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/thread

# Writing fast and efficient MicroPython
# https://www.youtube.com/watch?v=hHec4qL00x0

def set_global_exception():
    def handle_exception(loop, context):
        import sys
        sys.print_exception(context["exception"])
        sys.exit()
    loop = uasyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


async def main():
    set_global_exception()  # Debug aid
    mvp_statemachine = StateMachine(player_buzz_profile,
                                    states_mvp,
                                    transitions_mvp,
                                    BOOTING)

    await mvp_statemachine.start()  # Non-terminating method


# here the code starts running
try:
    uasyncio.new_event_loop()  # clear the loop on startup, so that only our stuff is running
    uasyncio.run(main())
finally:
    uasyncio.new_event_loop()  # Clear retained state
