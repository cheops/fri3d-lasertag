import uasyncio
import time

from hardware import blaster, boot_button
from profiles_common import Profile
from mvp import BOOTING, PRACTICING, HIDING, PLAYING, FINISHING, PRESTART
from mvp import DEAD, COUNTDOWN_END
from mvp import playing_time, hiding_time, hit_damage
from display import DisplayFlag, DisplayPlayer
from teams import REX, GIGGLE, BUZZ, team_blaster
from booting_screen import monitor as booting_monitor


class FlagAndPlayer(Profile):
    def __init__(self, team):
        super().__init__()
        self.name = self.__class__.__name__ + ' ' + team
        self._team = team
        self.health = 100
        self._current_state_tasks = []

    def run(self, state, statemachine):
        print(state)
        if state == BOOTING:
            _booting(statemachine)
        elif state == PRACTICING:
            self._practicing(statemachine)
        elif state == HIDING:
            self._hiding(statemachine)
        elif state == PLAYING:
            self._playing(statemachine)
        elif state == FINISHING:
            self._finishing(statemachine)

    def _practicing(self, statemachine):
        blaster.blaster.set_team(team_blaster[self._team])

    def _hiding(self, statemachine):
        pass

    def _playing(self, statemachine):
        pass

    def _finishing(self, statemachine):
        pass

    def stop_current_tasks(self):
        for t in self._current_state_tasks:
            t.cancel()


class Flag(FlagAndPlayer):

    def _practicing(self, statemachine):
        super()._practicing(statemachine)
        my_display = DisplayFlag(self._team)
        my_display.draw_upper_left(self.health)
        my_display.draw_middle(0)
        uasyncio.run(_monitor_button_simulate_prestart(statemachine))
        blaster.blaster.set_trigger_action(disable=True)

    def _hiding(self, statemachine):
        my_display = DisplayFlag(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_middle(0)
        blaster.blaster.set_trigger_action(disable=True)

        task = uasyncio.create_task(_blink_team_led())
        self._current_state_tasks.append(task)

        uasyncio.run(_countdown(my_display, hiding_time, statemachine))

    def _playing(self, statemachine):
        my_display = DisplayFlag(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_middle(0)
        blaster.blaster.set_trigger_action(disable=True)

        uasyncio.run(_countdown(my_display, playing_time, statemachine))
        uasyncio.run(self._monitor_blaster(my_display, statemachine))

    async def _monitor_blaster(self, my_display, statemachine):
        while True:
            uasyncio.sleep(100)
            result = blaster.blaster.get_blaster_shot()
            if result:
                self.health -= hit_damage
                my_display.draw_upper_left(self.health)
                if self.health <= 0:
                    statemachine.trigger(DEAD)
                    break


class Player(FlagAndPlayer):

    def _practicing(self, statemachine):
        super()._practicing(statemachine)
        my_display = DisplayPlayer(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_upper_right(100)
        my_display.draw_middle(0)
        uasyncio.run(_monitor_button_simulate_prestart(statemachine))

    def _hiding(self, statemachine):
        my_display = DisplayPlayer(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_upper_right(100)
        my_display.draw_middle(0)
        blaster.blaster.set_trigger_action(disable=True)

        task = uasyncio.create_task(_blink_team_led())
        self._current_state_tasks.append(task)

        uasyncio.run(_countdown(my_display, hiding_time, statemachine))

    def _playing(self, statemachine):
        my_display = DisplayPlayer(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_upper_right(100)
        my_display.draw_middle(0)
        blaster.blaster.set_trigger_action(disable=False)

        uasyncio.run(_countdown(my_display, playing_time, statemachine))
        uasyncio.run(self._monitor_blaster(my_display, statemachine))

    async def _monitor_blaster(self, my_display, statemachine):
        while True:
            uasyncio.sleep(100)
            result = blaster.blaster.get_blaster_shot()
            if result:
                self.health -= hit_damage
                my_display.draw_upper_left(self.health)
                if self.health <= 0:
                    statemachine.trigger(DEAD)
                    break


def _booting(statemachine):
    uasyncio.run(booting_monitor(statemachine))


async def _countdown(countdown_display, countdown_seconds, statemachine):
    start = time.ticks_ms()  # get millisecond counter

    previous_remaining_seconds = None
    while True:
        uasyncio.sleep(100)
        delta = time.ticks_diff(time.ticks_ms(), start)  # compute time difference

        remaining_seconds = int((countdown_seconds * 1000 - delta) / 1000)
        if remaining_seconds != previous_remaining_seconds:
            previous_remaining_seconds = remaining_seconds
            countdown_display.draw_middle(remaining_seconds)
        if delta >= countdown_seconds * 1000:
            statemachine.trigger(COUNTDOWN_END)
            break


async def _monitor_button_simulate_prestart(statemachine):
    while True:
        uasyncio.sleep(100)
        if boot_button.value() == 0:
            statemachine.trigger(PRESTART)
            break


player_rex_profile = Player(REX)
player_giggle_profile = Player(GIGGLE)
player_buzz_profile = Player(BUZZ)
flag_rex_profile = Flag(REX)
flag_giggle_profile = Flag(GIGGLE)
flag_buzz_profile = Flag(BUZZ)
