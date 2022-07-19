import uasyncio
import time

from hardware import blaster, boot_button
from profiles_common import Profile
from mvp import BOOTING, PRACTICING, HIDING, PLAYING, FINISHING, PRESTART, BOOT
from mvp import DEAD, COUNTDOWN_END
from mvp import playing_time, hiding_time, hit_damage
from display import Display, DisplayFlag, DisplayPlayer
from teams import REX, GIGGLE, BUZZ, team_blaster
from booting_screen import monitor as monitor_booting
from monitor_blaster import monitor_blaster
from monitor_countdown import monitor_countdown


class FlagAndPlayer(Profile):
    def __init__(self, team):
        super().__init__()
        self._my_display: Display | None = None
        self.name = self.__class__.__name__ + ' ' + team
        self._team = team
        self.health = 100
        self._current_state_tasks = []

    def run(self, state, statemachine):
        print(state)
        if state == BOOTING:
            uasyncio.run(monitor_booting(statemachine))
        elif state == PRACTICING:
            self._practicing(statemachine)
        elif state == HIDING:
            self._hiding(statemachine)
        elif state == PLAYING:
            self._playing(statemachine)
        elif state == FINISHING:
            self._finishing(statemachine)

    def stop_current_tasks(self):
        while len(self._current_state_tasks):
            t = self._current_state_tasks.pop()
            t.cancel()

    def _practicing(self, statemachine):
        pass

    def _hiding(self, statemachine):
        pass

    def _playing(self, statemachine):
        pass

    def _finishing(self, statemachine):
        pass

    async def _monitor_blaster(self, statemachine):

        def _got_hit():
            """"return True when dead, False otherwise"""
            self.health -= hit_damage
            self._my_display.draw_upper_left(self.health)
            if self.health <= 0:
                statemachine.trigger(DEAD)
                return True
            else:
                return False

        await monitor_blaster(self._team, _got_hit)


class Flag(FlagAndPlayer):
    def __init__(self, team):
        super().__init__(team)
        self._my_display = DisplayFlag(self._team)

    def _practicing(self, statemachine):
        blaster.blaster.set_team(team_blaster[self._team])
        blaster.blaster.set_trigger_action(disable=True)
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Practicing")
        self._my_display.draw_middle(0)
        
        t_blaster = uasyncio.create_task(self._monitor_blaster(statemachine))
        self._current_state_tasks.append(t_blaster)
        
        def button_press():
            statemachine.trigger(PRESTART)
         
        uasyncio.run(_monitor_button_press(button_press))

    def _hiding(self, statemachine):
        blaster.blaster.set_trigger_action(disable=True)
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Hiding")

        def handle_countdown_end():
            statemachine.trigger(COUNTDOWN_END)

        uasyncio.run(monitor_countdown(hiding_time, handle_countdown_end, self._my_display.draw_middle))

    def _playing(self, statemachine):
        blaster.blaster.set_trigger_action(disable=True)
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Playing")
        t_blaster = uasyncio.create_task(self._monitor_blaster(statemachine))
        self._current_state_tasks.append(t_blaster)

        def handle_countdown_end():
            statemachine.trigger(COUNTDOWN_END)

        uasyncio.run(monitor_countdown(playing_time, handle_countdown_end, self._my_display.draw_middle))

    def _finishing(self, statemachine):
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Finishing")

        def button_press():
            statemachine.trigger(BOOT)
        uasyncio.run(_monitor_button_press(button_press))


class Player(FlagAndPlayer):

    def __init__(self, team):
        super().__init__(team)
        self._my_display: DisplayPlayer = DisplayPlayer(self._team)

    def _practicing(self, statemachine):
        blaster.blaster.set_team(team_blaster[self._team])
        blaster.blaster.set_trigger_action(disable=False)
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(100)
        self._my_display.draw_static_middle("Practicing")
        self._my_display.draw_middle(0)

        t_blaster = uasyncio.create_task(self._monitor_blaster(statemachine))
        self._current_state_tasks.append(t_blaster)

        def button_press():
            statemachine.trigger(PRESTART)

        uasyncio.run(_monitor_button_press(button_press))


    def _hiding(self, statemachine):
        blaster.blaster.set_trigger_action(disable=True)
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(100)
        self._my_display.draw_static_middle("Hiding")

        def handle_countdown_end():
            statemachine.trigger(COUNTDOWN_END)

        uasyncio.run(monitor_countdown(hiding_time, handle_countdown_end, self._my_display.draw_middle))

    def _playing(self, statemachine):
        blaster.blaster.set_trigger_action(disable=False)
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(100)
        self._my_display.draw_static_middle("Playing")
        t_blaster = uasyncio.create_task(self._monitor_blaster(statemachine))
        self._current_state_tasks.append(t_blaster)

        def handle_countdown_end():
            statemachine.trigger(COUNTDOWN_END)

        uasyncio.run(monitor_countdown(playing_time, handle_countdown_end, self._my_display.draw_middle))

    def _finishing(self, statemachine):
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(100)
        self._my_display.draw_static_middle("Finishing")

        def button_press():
            statemachine.trigger(BOOT)
        uasyncio.run(_monitor_button_press(button_press))


async def _monitor_button_press(button_press_fnc):
    last_value = boot_button.value()
    while True:
        await uasyncio.sleep(0.1)
        new_value = boot_button.value()
        if last_value != new_value:
            last_value = new_value
            if new_value == 0:
                print("button pressed")
                button_press_fnc()
                break


player_rex_profile = Player(REX)
player_giggle_profile = Player(GIGGLE)
player_buzz_profile = Player(BUZZ)
flag_rex_profile = Flag(REX)
flag_giggle_profile = Flag(GIGGLE)
flag_buzz_profile = Flag(BUZZ)
