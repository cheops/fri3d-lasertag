import uasyncio

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
        self._new_event = None

    def set_new_event(self, new_event):
        self._new_event = new_event

    def run(self, state):
        print(state)
        if state == BOOTING:
            self._booting()
        elif state == PRACTICING:
            self._practicing()
        elif state == HIDING:
            self._hiding()
        elif state == PLAYING:
            self._playing()
        elif state == FINISHING:
            self._finishing()

        return uasyncio.run(self._forever())

    async def _forever(self):
        while self._new_event is None:
            await uasyncio.sleep(0.1)
        self.stop_current_tasks()
        new_event = self._new_event
        self.set_new_event(None)
        return new_event

    def stop_current_tasks(self):
        while len(self._current_state_tasks):
            t = self._current_state_tasks.pop()
            t.cancel()

    def _booting(self):
        t_monitor = uasyncio.create_task(monitor_booting(self.set_new_event, self))
        self._current_state_tasks.append(t_monitor)

    def _practicing(self):
        pass

    def _hiding(self):
        pass

    def _playing(self):
        pass

    def _finishing(self):
        pass

    async def _monitor_blaster(self):

        def _got_hit():
            """"return True when dead, False otherwise"""
            self.health -= hit_damage
            self._my_display.draw_upper_left(self.health)
            if self.health <= 0:
                self.set_new_event(DEAD)
                return True
            else:
                return False

        await monitor_blaster(self._team, _got_hit)


class Flag(FlagAndPlayer):
    def __init__(self, team):
        super().__init__(team)
        self._my_display = DisplayFlag(self._team)

    def _practicing(self):
        blaster.blaster.set_team(team_blaster[self._team])
        blaster.blaster.set_trigger_action(disable=True)
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Practicing")
        self._my_display.draw_middle(0)

        t_blaster = uasyncio.create_task(self._monitor_blaster())
        self._current_state_tasks.append(t_blaster)

        def button_press():
            self.set_new_event(PRESTART)

        t_button = uasyncio.create_task(_monitor_button_press(button_press))
        self._current_state_tasks.append(t_button)

    def _hiding(self):
        blaster.blaster.set_trigger_action(disable=True)
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Hiding")

        def handle_countdown_end():
            self.set_new_event(COUNTDOWN_END)

        t_countdown = uasyncio.create_task(monitor_countdown(hiding_time, handle_countdown_end, self._my_display.draw_middle))
        self._current_state_tasks.append(t_countdown)

    def _playing(self):
        blaster.blaster.set_trigger_action(disable=True)
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Playing")
        t_blaster = uasyncio.create_task(self._monitor_blaster())
        self._current_state_tasks.append(t_blaster)

        def handle_countdown_end():
            self.set_new_event(COUNTDOWN_END)

        t_countdown = uasyncio.create_task(monitor_countdown(playing_time, handle_countdown_end, self._my_display.draw_middle))
        self._current_state_tasks.append(t_countdown)

    def _finishing(self):
        blaster.blaster.set_trigger_action(disable=True)
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Finishing")

        def button_press():
            self.set_new_event(BOOT)

        t_button = uasyncio.create_task(_monitor_button_press(button_press))
        self._current_state_tasks.append(t_button)


class Player(FlagAndPlayer):

    def __init__(self, team):
        super().__init__(team)
        self._my_display: DisplayPlayer = DisplayPlayer(self._team)

    def _practicing(self):
        blaster.blaster.set_team(team_blaster[self._team])
        blaster.blaster.set_trigger_action(disable=False)
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(100)
        self._my_display.draw_static_middle("Practicing")
        self._my_display.draw_middle(0)

        t_blaster = uasyncio.create_task(self._monitor_blaster())
        self._current_state_tasks.append(t_blaster)

        def button_press():
            self.set_new_event(PRESTART)

        t_button = uasyncio.create_task(_monitor_button_press(button_press))
        self._current_state_tasks.append(t_button)

    def _hiding(self):
        blaster.blaster.set_trigger_action(disable=True)
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(100)
        self._my_display.draw_static_middle("Hiding")

        def handle_countdown_end():
            self.set_new_event(COUNTDOWN_END)

        t_countdown = uasyncio.create_task(monitor_countdown(hiding_time, handle_countdown_end, self._my_display.draw_middle))
        self._current_state_tasks.append(t_countdown)

    def _playing(self):
        blaster.blaster.set_trigger_action(disable=False)
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(100)
        self._my_display.draw_static_middle("Playing")
        t_blaster = uasyncio.create_task(self._monitor_blaster())
        self._current_state_tasks.append(t_blaster)

        def handle_countdown_end():
            self.set_new_event(COUNTDOWN_END)

        t_countdown = uasyncio.create_task(monitor_countdown(playing_time, handle_countdown_end, self._my_display.draw_middle))
        self._current_state_tasks.append(t_countdown)

    def _finishing(self):
        blaster.blaster.set_trigger_action(disable=True)
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(100)
        self._my_display.draw_static_middle("Finishing")

        def button_press():
            self.set_new_event(BOOT)

        t_button = uasyncio.create_task(_monitor_button_press(button_press))
        self._current_state_tasks.append(t_button)


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
