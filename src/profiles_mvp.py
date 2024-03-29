import uasyncio
from time import sleep

from hardware import blaster, boot_button
from profiles_common import Profile
from mvp import BOOTING, PRACTICING, HIDING, PLAYING, FINISHING
from mvp import DEAD, COUNTDOWN_END, NEXT_ROUND, PRESTART, BOOT
from mvp import playing_time, hiding_time, hit_damage, hit_timeout, shot_ammo, practicing_channel, playing_channel , invalid_channel
from display import Display, DisplayFlag, DisplayPlayer
from effects import effect_R2D2, pixels_clear, effect_reload
from teams import REX, GIGGLE, BUZZ, team_blaster
from booting_screen import monitor_booting
from monitor_ir import monitor_blaster, clear_blaster_buffer, monitor_badge, clear_badge_buffer
from monitor_countdown import monitor_countdown
from message_parser import BleMessage, parse_flag_prestart_msg, parse_player_prestart_msg
from monitor_mqtt import publish_mqtt_flag, publish_mqtt_player, \
    subscribe_flag_prestart, subscribe_player_prestart, subscribe_device_stop
from monitor_ble import ble_listener, PRESTART_TYPE, NEXT_ROUND_TYPE


class FlagAndPlayer(Profile):
    def __init__(self, team):
        super().__init__()
        self._my_display: Display | None = None
        self.name = self.__class__.__name__ + ' ' + team
        self._team = team
        self.health = 100
        self._remaining_seconds = 0
        self._current_state_tasks = []
        self._new_event = None

        self._hiding_time = hiding_time
        self._playing_time = playing_time
        self._hit_damage = hit_damage
        self._hit_timeout = hit_timeout
        self._practicing_channel = practicing_channel
        self._playing_channel = playing_channel
        self._mqtt_game_id = 0

        self._mqtt_during_all = False
        self._mqtt_during_playing = False

    def set_new_event(self, new_event):
        if self._new_event is None or new_event is None:  # avoid overwriting of new_event, any next new_event is ignored, except for clearing
            self._new_event = new_event

    async def run(self, state):
        # if run finishes, it should return a new_event
        print("running state:", state)
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

        #return uasyncio.run(self._forever())
        # we should run forever non-blocking and return with a new_event
        return await self._forever()

    async def _forever(self):
        while self._new_event is None:
            await uasyncio.sleep(0.5)
        await self.stop_current_state_tasks()
        new_event = self._new_event
        self.set_new_event(None)
        return new_event

    async def stop_current_state_tasks(self):
        for t in self._current_state_tasks:
            t.cancel()
        while len(self._current_state_tasks):
            t = self._current_state_tasks.pop()
            await t

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


class Flag(FlagAndPlayer):
    def __init__(self, team):
        super().__init__(team)
        self._my_display = DisplayFlag(self._team)

    async def _monitor_badge(self, channel):

        def _got_hit():
            """"return True when dead, False otherwise"""
            if self.health > 0:
                self.health -= self._hit_damage
            if self.health < 0:
                self.health = 0
            self._my_display.draw_upper_left(self.health)
            effect_R2D2()
            pixels_clear()
            uasyncio.wait_for(sleep(self._hit_timeout), self._hit_timeout + 1)
            clear_badge_buffer()
            if self.health <= 0:
                self.set_new_event(DEAD)
                return True
            else:
                return False

        await monitor_badge(self._team, channel, _got_hit)

    def _practicing(self):
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_team, (team_blaster[self._team],)), self._hit_timeout)
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': True}), self._hit_timeout)
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_channel, (self._practicing_channel, )), self._hit_timeout)
        clear_badge_buffer()
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Practicing")
        self._my_display.draw_middle(0)

        t_badge = uasyncio.create_task(self._monitor_badge(self._practicing_channel))
        self._current_state_tasks.append(t_badge)

        def button_press():
            self.set_new_event(PRESTART)

        t_button = uasyncio.create_task(_monitor_button_press(button_press))
        self._current_state_tasks.append(t_button)

        # ble callback for prestart
        def received_ble_prestart_msg(msg):
            ble_msg = BleMessage(msg)
            print("parsed_ble_msg", ble_msg)
            self._hiding_time = ble_msg.hiding_time
            self._playing_time = ble_msg.playing_time
            self._hit_damage = ble_msg.hit_damage
            self._hit_timeout = ble_msg.hit_timeout
            #self._shot_ammo = ble_msg.shot_ammo
            self._practicing_channel = ble_msg.practicing_channel
            self._playing_channel = ble_msg.playing_channel
            self._mqtt_game_id = ble_msg.mqtt_game_id
            self._mqtt_during_playing = ble_msg.mqtt_during_playing
            self.set_new_event(PRESTART)

        t_ble = uasyncio.create_task(ble_listener(PRESTART_TYPE, received_ble_prestart_msg))
        self._current_state_tasks.append(t_ble)

        if self._mqtt_during_all:
            def parse_prestart_msg(mqtt_msg):
                p = parse_flag_prestart_msg(mqtt_msg)
                self._hiding_time = p.get('hiding_time', hiding_time)
                self._playing_time = p.get('playing_time', playing_time)
                self._hit_damage = p.get('hit_damage', hit_damage)
                self._hit_timeout = p.get('hit_timeout', hit_timeout)
                self._playing_channel = p.get('playing_channel', playing_channel)
                self._mqtt_game_id = p.get('mqtt_game_id', self._mqtt_game_id)
                self._mqtt_during_playing = p.get('mqtt_during_playing', False)
                self.set_new_event(PRESTART)

            t_mqtt = uasyncio.create_task(subscribe_flag_prestart(parse_prestart_msg))
            self._current_state_tasks.append(t_mqtt)

    def _hiding(self):
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_team, (team_blaster[self._team], )), self._hit_timeout)
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': True}), self._hit_timeout)
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_channel, (invalid_channel, )), self._hit_timeout)
        clear_badge_buffer()
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Hiding")

        def handle_countdown_end():
            self.set_new_event(COUNTDOWN_END)

        t_countdown = uasyncio.create_task(monitor_countdown(self._hiding_time, handle_countdown_end, self._my_display.draw_middle))
        self._current_state_tasks.append(t_countdown)

    def _playing(self):
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_team, (team_blaster[self._team],)), self._hit_timeout)
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': True}), self._hit_timeout)
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_channel, (self._playing_channel,)), self._hit_timeout)
        clear_badge_buffer()
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Playing")
        t_badge = uasyncio.create_task(self._monitor_badge(self._playing_channel))
        self._current_state_tasks.append(t_badge)

        def handle_countdown_end():
            self.set_new_event(COUNTDOWN_END)

        def handle_countdown_update(remaining_seconds):
            self._my_display.draw_middle(remaining_seconds)
            self._remaining_seconds = remaining_seconds

        t_countdown = uasyncio.create_task(monitor_countdown(self._playing_time, handle_countdown_end, handle_countdown_update))
        self._current_state_tasks.append(t_countdown)

        if self._mqtt_during_all and self._mqtt_during_playing:
            def get_health():
                return self.health

            def get_remaining_seconds():
                return self._remaining_seconds

            t_mqtt = uasyncio.create_task(publish_mqtt_flag(self._team, self._mqtt_game_id, get_health, get_remaining_seconds))
            self._current_state_tasks.append(t_mqtt)

    def _finishing(self):
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_team, (team_blaster[self._team],)), self._hit_timeout)
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': True}), self._hit_timeout)
        #uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_channel, (invalid_channel, )), self._hit_timeout)
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_static_middle("Finishing")
        self._my_display.draw_middle(self._remaining_seconds)

        def button_press():
            self.set_new_event(BOOT)

        t_button = uasyncio.create_task(_monitor_button_press(button_press))
        self._current_state_tasks.append(t_button)

        def ble_parse_next_round(msg):
            ble_msg = BleMessage(msg)
            if ble_msg.message_type == NEXT_ROUND_TYPE:
                self.set_new_event(NEXT_ROUND)

        t_ble = uasyncio.create_task(ble_listener(NEXT_ROUND_TYPE, ble_parse_next_round))
        self._current_state_tasks.append(t_ble)

        if self._mqtt_during_all:
            def parse_device_stop(mqtt_msg):
                if mqtt_msg == "stop":
                    self.set_new_event(NEXT_ROUND)

            t_mqtt = uasyncio.create_task(subscribe_device_stop(parse_device_stop))
            self._current_state_tasks.append(t_mqtt)


class Player(FlagAndPlayer):

    def __init__(self, team):
        super().__init__(team)
        self._my_display: DisplayPlayer = DisplayPlayer(self._team)
        self._shot_ammo = shot_ammo
        self._hits = 0
        self._shots = 0

    async def _monitor_blaster(self):

        def _got_hit():
            """"return True when dead, False otherwise"""
            self._hits += 1
            if self.health > 0:
                self.health -= self._hit_damage
            if self.health < 0:
                self.health = 0
            self._my_display.draw_upper_left(self.health)
            uasyncio.wait_for(sleep(self._hit_timeout), self._hit_timeout + 1)  # sleep long enough for the blaster to be responsive
            clear_blaster_buffer()
            if self.health <= 0:
                self.set_new_event(DEAD)
                return True
            else:
                return False

        async def _shot():
            async def reload_display():
                for ammo in range(0, 100):
                    self.ammo = ammo
                    self._my_display.draw_upper_right(self.ammo)
                    await uasyncio.sleep(0.1)

            self._shots += 1
            if self.ammo > 0:
                self.ammo -= self._shot_ammo
            if self.ammo < 0:
                self.ammo = 0
            self._my_display.draw_upper_right(self.ammo)
            if self.ammo <= 0:
                uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': True}), self._hit_timeout)
                uasyncio.wait_for(effect_reload(), 11)
                t = uasyncio.create_task(reload_display())
                await t
                self.ammo = 100
                self._my_display.draw_upper_right(self.ammo)
                uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': False}), self._hit_timeout)

        await monitor_blaster(self._team, _got_hit, _shot)

    def _practicing(self):
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_team, (team_blaster[self._team],)), self._hit_timeout)
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': False}), self._hit_timeout)
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_channel, (self._practicing_channel,)), self._hit_timeout)
        clear_blaster_buffer()
        self._hits = 0
        self._shots = 0
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self.ammo = 100
        self._my_display.draw_upper_right(self.ammo)
        self._my_display.draw_static_middle("Practicing")
        self._my_display.draw_middle(0)

        t_blaster = uasyncio.create_task(self._monitor_blaster())
        self._current_state_tasks.append(t_blaster)

        def button_press():
            self.set_new_event(PRESTART)

        t_button = uasyncio.create_task(_monitor_button_press(button_press))
        self._current_state_tasks.append(t_button)

        # ble callback for prestart
        def received_ble_prestart_msg(msg):
            ble_msg = BleMessage(msg)
            print("parsed_ble_msg", ble_msg)
            self._hiding_time = ble_msg.hiding_time
            self._playing_time = ble_msg.playing_time
            self._hit_damage = ble_msg.hit_damage
            self._hit_timeout = ble_msg.hit_timeout
            self._shot_ammo = ble_msg.shot_ammo
            self._practicing_channel = ble_msg.practicing_channel
            self._playing_channel = ble_msg.playing_channel
            self._mqtt_game_id = ble_msg.mqtt_game_id
            self._mqtt_during_playing = ble_msg.mqtt_during_playing
            self.set_new_event(PRESTART)

        t_ble = uasyncio.create_task(ble_listener(PRESTART_TYPE, received_ble_prestart_msg))
        self._current_state_tasks.append(t_ble)

        if self._mqtt_during_all:
            def parse_prestart_msg(mqtt_msg):
                p = parse_player_prestart_msg(mqtt_msg)
                self._hiding_time = p.get('hiding_time', hiding_time)
                self._playing_time = p.get('playing_time', playing_time)
                self._hit_damage = p.get('hit_damage', hit_damage)
                self._hit_timeout = p.get('hit_timeout', hit_timeout)
                self._shot_ammo = p.get('shot_ammo', shot_ammo)
                self._playing_channel = p.get('playing_channel', playing_channel)
                self._mqtt_game_id = p.get('mqtt_game_id', self._mqtt_game_id)
                self._mqtt_during_playing = p.get('mqtt_during_playing', False)
                self.set_new_event(PRESTART)

            t_mqtt = uasyncio.create_task(subscribe_player_prestart(parse_prestart_msg))
            self._current_state_tasks.append(t_mqtt)

    def _hiding(self):
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_team, (team_blaster[self._team],)), self._hit_timeout)
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': True}), self._hit_timeout)
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_channel, (invalid_channel,)), self._hit_timeout)
        clear_blaster_buffer()
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self.ammo = 100
        self._my_display.draw_upper_right(self.ammo)
        self._my_display.draw_static_middle("Hiding")

        def handle_countdown_end():
            self.set_new_event(COUNTDOWN_END)

        t_countdown = uasyncio.create_task(monitor_countdown(self._hiding_time, handle_countdown_end, self._my_display.draw_middle))
        self._current_state_tasks.append(t_countdown)

    def _playing(self):
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_team, (team_blaster[self._team],)), self._hit_timeout)
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': False}), self._hit_timeout)
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_channel, (self._playing_channel,)), self._hit_timeout)
        clear_blaster_buffer()
        self._hits = 0
        self._shots = 0
        self.health = 100
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self.ammo = 100
        self._my_display.draw_upper_right(self.ammo)
        self._my_display.draw_static_middle("Playing")
        t_blaster = uasyncio.create_task(self._monitor_blaster())
        self._current_state_tasks.append(t_blaster)

        def handle_countdown_end():
            self.set_new_event(COUNTDOWN_END)

        def handle_countdown_update(remaining_seconds):
            self._my_display.draw_middle(remaining_seconds)
            self._remaining_seconds = remaining_seconds

        t_countdown = uasyncio.create_task(monitor_countdown(self._playing_time, handle_countdown_end, handle_countdown_update))
        self._current_state_tasks.append(t_countdown)

        if self._mqtt_during_all and self._mqtt_during_playing:
            def get_health():
                return self.health

            def get_hits():
                return self._hits

            def get_shots():
                return self._shots

            def get_remaining_seconds():
                return self._remaining_seconds

            t_mqtt = uasyncio.create_task(publish_mqtt_player(self._team, self._mqtt_game_id, get_health, get_hits, get_shots, get_remaining_seconds))
            self._current_state_tasks.append(t_mqtt)

    def _finishing(self):
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_team, (team_blaster[self._team],)), self._hit_timeout)
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_trigger_action, kwargs={'disable': True}), self._hit_timeout)
        uasyncio.wait_for(to_blaster_with_retry(blaster.blaster.set_channel, (invalid_channel,)), self._hit_timeout)
        self._my_display.draw_initial()
        self._my_display.draw_upper_left(self.health)
        self._my_display.draw_upper_right(self.ammo)
        self._my_display.draw_static_middle("Finishing")
        self._my_display.draw_middle(self._remaining_seconds)

        def button_press():
            self.set_new_event(NEXT_ROUND)

        t_button = uasyncio.create_task(_monitor_button_press(button_press))
        self._current_state_tasks.append(t_button)

        def ble_parse_next_round(msg):
            ble_msg = BleMessage(msg)
            if ble_msg.message_type == NEXT_ROUND_TYPE:
                self.set_new_event(NEXT_ROUND)

        t_ble = uasyncio.create_task(ble_listener(NEXT_ROUND_TYPE, ble_parse_next_round))
        self._current_state_tasks.append(t_ble)

        if self._mqtt_during_all:
            def parse_device_stop(mqtt_msg):
                if mqtt_msg == "stop":
                    self.set_new_event(NEXT_ROUND)

            t_mqtt = uasyncio.create_task(subscribe_device_stop(parse_device_stop))
            self._current_state_tasks.append(t_mqtt)


def to_blaster_with_retry(fnc, args=(), kwargs=None):
    if kwargs is None:
        kwargs = {}
    # blaster returns True if success
    while not fnc(*args, **kwargs):
        sleep(0.1)


async def _monitor_button_press(button_press_fnc):
    try:
        last_value = boot_button.value()
        while True:
            await uasyncio.sleep(0.5)
            new_value = boot_button.value()
            if last_value != new_value:
                last_value = new_value
                if new_value == 0:
                    print("button pressed")
                    button_press_fnc()
                    break
    except uasyncio.CancelledError:
        pass

player_rex_profile = Player(REX)
player_giggle_profile = Player(GIGGLE)
player_buzz_profile = Player(BUZZ)
flag_rex_profile = Flag(REX)
flag_giggle_profile = Flag(GIGGLE)
flag_buzz_profile = Flag(BUZZ)
