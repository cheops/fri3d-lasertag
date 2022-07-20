import vga1_16x32 as font_32
import st7789py as st7789
import time
import uasyncio as asyncio

from hardware import neopixels, tft, touch_0, touch_1, touch_2, boot_button
from mvp import CONFIRM_PROFILE
from profiles_common import Profile


class Touch:
    trigger_level = 60
    sample_time = 10

    def __init__(self, touch, led):
        self.touch = touch
        # press function
        self._pf = None
        # release function
        self._rf = None
        self._led = led

        # Get initial state
        self.state = self.rawstate()
        # Thread runs forever
        self._run = asyncio.create_task(self.touchcheck())

    def press_func(self, func):
        self._pf = func

    def release_func(self, func):
        self._rf = func

    # Current non-debounced logical button state: True == pressed
    def rawstate(self):
        rel_level = max(self.touch.read() - self.trigger_level, 0)
        # print(self._led, rel_level)
        if rel_level > 0:
            neopixels[self._led] = (50 - min(50, rel_level), 0, 15)
        else:
            neopixels[self._led] = (0, 50, 0)
        neopixels.write()
        return self.touch.read() < self.trigger_level

    # Return current state of switch (0 = pressed)
    def __call__(self):
        return self.state

    async def touchcheck(self):
        while True:
            try:
                touched = self.rawstate()
                if touched != self.state:
                    # State has changed: act on it now.
                    self.state = touched
                    if touched is True and self._pf:
                        self._pf()
                    elif touched is False and self._rf:
                        self._rf()
            except ValueError:
                pass

            await asyncio.sleep_ms(Touch.sample_time)

    def deinit(self):
        self._run.cancel()
        neopixels[self._led] = (0, 0, 0)
        neopixels.write()


class ProfilesList:
    max_profiles_display = 6
    highlight_color = st7789.color565(200, 0, 0)
    not_highlight_color = st7789.color565(150, 150, 150)

    def __init__(self, initial_profile):
        self.profiles = Profile.find_profiles()

        self.current_profile = 0
        for i, p in enumerate(self.profiles):
            if p == initial_profile:
                self.current_profile = i

        self._touch_tasks = []
        self._current_start = 0
        self._chosen = False
        tft.fill(st7789.BLACK)
        self._buttons()
        self._show()

    def _buttons(self):
        tft.text(font_32, '0:<', 0, 240 - font_32.HEIGHT, ProfilesList.not_highlight_color)
        touch_left = Touch(touch_0, 0)
        touch_left.press_func(self._prv)
        self._touch_tasks.append(touch_left)

        tft.text(font_32, '1:OK', 120 - 2 * font_32.WIDTH, 240 - font_32.HEIGHT,
                 ProfilesList.not_highlight_color)
        touch_middle = Touch(touch_1, 1)
        touch_middle.release_func(self.ok)
        self._touch_tasks.append(touch_middle)

        tft.text(font_32, '2:>', 240 - 3 * font_32.WIDTH, 240 - font_32.HEIGHT,
                 ProfilesList.not_highlight_color)
        touch_right = Touch(touch_2, 2)
        touch_right.press_func(self._nxt)
        self._touch_tasks.append(touch_right)

    def has_chosen(self):
        return self._chosen

    def stop_touch_tasks(self):
        for t in self._touch_tasks:
            t.deinit()

    def _show(self):
        tft.fill_rect(0, 0, 240, 240 - 32, st7789.BLACK)

        start = 0
        for i in range(max(self.current_profile - 2, 0),
                       min(self.current_profile + ProfilesList.max_profiles_display, len(self.profiles))):
            color = ProfilesList.not_highlight_color
            if i == self.current_profile:
                color = ProfilesList.highlight_color
                tft.text(font_32, '>', 0, start * font_32.HEIGHT, color)
            tft.text(font_32, self.profiles[i].name, font_32.WIDTH, start * font_32.HEIGHT, color)
            start += 1

    def _prv(self):
        if self.current_profile > 0:
            self.current_profile -= 1
            self._show()

    def _nxt(self):
        if self.current_profile < len(self.profiles) - 1:
            self.current_profile += 1
            self._show()

    def ok(self):
        new_profile = self.profiles[self.current_profile]
        print(new_profile)
        CONFIRM_PROFILE.set_new_model(new_profile)
        self._chosen = True


def boot_screen_countdown(countdown_seconds):
    tft.fill(st7789.BLACK)
    row = 0
    tft.text(font_32, 'to select', 0, row * font_32.HEIGHT)
    row += 1
    tft.text(font_32, 'a new profile', 0, row * font_32.HEIGHT)
    row += 1
    tft.text(font_32, 'hold', 0, row * font_32.HEIGHT)
    row += 1
    tft.text(font_32, 'BOOT button', 0, row * font_32.HEIGHT)
    row += 1

    for i in range(countdown_seconds, -1, -1):
        if boot_button.value() == 0:
            # button pressed
            break
        tft.fill_rect(0, row * font_32.HEIGHT, font_32.WIDTH, font_32.HEIGHT, st7789.BLACK)
        tft.text(font_32, str(i), 0, row * font_32.HEIGHT)
        time.sleep(1)


async def monitor(set_new_event_fnc, initial_profile):
    boot_screen_countdown(3)
    # quick check, if button is not pressed, move on
    if boot_button.value() == 1:
        print('button released initially')
        if set_new_event_fnc:
            set_new_event_fnc(CONFIRM_PROFILE)
        return

    profiles_list = ProfilesList(initial_profile)

    last_button_value = boot_button.value()
    while True:
        new_value = boot_button.value()
        if new_value != last_button_value and new_value == 1:
            last_button_value = new_value
            print('button released')
            profiles_list.ok()
            profiles_list.stop_touch_tasks()
            if set_new_event_fnc:
                set_new_event_fnc(CONFIRM_PROFILE)
            break
        if new_value != last_button_value and new_value == 0:
            last_button_value = new_value
            print('button pressed')

        if profiles_list.has_chosen():
            print('profile chosen')
            profiles_list.ok()
            profiles_list.stop_touch_tasks()
            if set_new_event_fnc:
                set_new_event_fnc(CONFIRM_PROFILE)
            break

        await asyncio.sleep_ms(10)


# asyncio.run(monitor(None))

