import uasyncio
import time

import hardware
import game_profiles
import mvp
import display
import teams
import booting_screen


class FlagAndPlayer(game_profiles.Profile):
    def __init__(self, team):
        super().__init__()
        self.name = self.__class__.__name__ + ' ' + team
        self._team = team
        self.health = 100

    def run(self, state, statemachine):
        print(state)
        if state == mvp.BOOTING:
            _booting(statemachine)
        elif state == mvp.PRACTICING:
            self._practicing(statemachine)
        elif state == mvp.HIDING:
            self._hiding(statemachine)
        elif state == mvp.PLAYING:
            self._playing(statemachine)
        elif state == mvp.FINISHING:
            self._finishing(statemachine)

    def _practicing(self, statemachine):
        hardware.blaster.blaster.set_team(teams.team_blaster(self._team))

    def _hiding(self, statemachine):
        pass

    def _playing(self, statemachine):
        pass

    def _finishing(self, statemachine):
        pass


class Flag(FlagAndPlayer):

    def _practicing(self, statemachine):
        super()._practicing(statemachine)
        my_display = display.DisplayFlag(self._team)
        my_display.draw_upper_left(self.health)
        my_display.draw_middle(0)

    def _hiding(self, statemachine):
        my_display = display.DisplayFlag(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_middle(0)

        uasyncio.run(_countdown(my_display, mvp.hiding_time, statemachine))

    def _playing(self, statemachine):
        my_display = display.DisplayFlag(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_middle(0)

        uasyncio.run(_countdown(my_display, mvp.playing_time, statemachine))
        uasyncio.run(self._monitor_blaster(my_display, statemachine))

    async def _monitor_blaster(self, my_display, statemachine):
        while True:
            uasyncio.sleep(100)
            result = hardware.blaster.blaster.get_blaster_shot()
            if result:
                self.health -= mvp.hit_damage
                my_display.draw_upper_left(self.health)
                if self.health <= 0:
                    statemachine.trigger(mvp.DEAD)
                    break


class Player(FlagAndPlayer):

    def _practicing(self, statemachine):
        super()._practicing(statemachine)
        my_display = display.DisplayPlayer(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_upper_right(100)
        my_display.draw_middle(0)

    def _hiding(self, statemachine):
        my_display = display.DisplayPlayer(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_upper_right(100)
        my_display.draw_middle(0)

        uasyncio.run(_countdown(my_display, mvp.hiding_time, statemachine))

    def _playing(self, statemachine):
        my_display = display.DisplayPlayer(self._team)
        my_display.draw_upper_left(100)
        my_display.draw_upper_right(100)
        my_display.draw_middle(0)

        uasyncio.run(_countdown(my_display, mvp.playing_time, statemachine))
        uasyncio.run(self._monitor_blaster(my_display, statemachine))

    async def _monitor_blaster(self, my_display, statemachine):
        while True:
            uasyncio.sleep(100)
            result = hardware.blaster.blaster.get_blaster_shot()
            if result:
                self.health -= mvp.hit_damage
                my_display.draw_upper_left(self.health)
                if self.health <= 0:
                    statemachine.trigger(mvp.DEAD)
                    break


def _booting(statemachine):
    uasyncio.run(booting_screen.monitor(statemachine))


async def _countdown(countdown_display, countdown_seconds, statemachine):
    start = time.ticks_ms()  # get millisecond counter

    while True:
        uasyncio.sleep(100)
        delta = time.ticks_diff(time.ticks_ms(), start)  # compute time difference

        remaining_seconds = int((countdown_seconds * 1000 - delta) / 1000)
        countdown_display.draw_middle(remaining_seconds)
        if delta >= countdown_seconds * 1000:
            statemachine.trigger(mvp.COUNTDOWN_END)


player_rex_profile = Player(teams.REX)
player_giggle_profile = Player(teams.GIGGLE)
player_buzz_profile = Player(teams.BUZZ)
flag_rex_profile = Flag(teams.REX)
flag_giggle_profile = Flag(teams.GIGGLE)
flag_buzz_profile = Flag(teams.BUZZ)
