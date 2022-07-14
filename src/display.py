import st7789
import time
from machine import SoftI2C, Pin, SPI
from lis2hh12 import LIS2HH12, SF_G

import teams

import chango_16 as font_16
import chango_32 as font_32
import chango_64 as font_64


class Display:
    """
     Display class that divides the screen in [upper_left, upper_right, middle, bottom]

     screen micropython driver used is https://github.com/russhughes/st7789_mpy
     more documentation about it's methods https://github.com/devbis/st7789_mpy

      ST7789.rect(x, y, width, height, color)
      ST7789.hline(x, y, length, color)
      ST7789.vline(x, y, length, color)
      ST7789.hline(x, y, length, color)

      text(font, s, x, y[, fg, bg])
      write(bitmap_font, s, x, y[, fg, bg, background_tuple, fill_flag])

     basic screen layout:
        +---------+--------+
        | Health  | Ammo   |
        |  100%   | 100%   |
        +---------+--------+
        |    countdown     |
        |       0:00       |
        +------------------+
        |    player buzz   |
        +------------------+
     borders are 8 pixels wide
    """
    _color_rex = st7789.color565(255, 0, 0)
    _color_giggle = st7789.color565(0, 140, 0)
    _color_buzz = st7789.color565(0, 0, 210)

    _team_colors = {teams.REX: _color_rex,
                    teams.GIGGLE: _color_giggle,
                    teams.BUZZ: _color_buzz}

    _width = 8
    _bg_color = st7789.WHITE

    def __init__(self, team):
        self._team = team
        self._color = self._team_colors[self._team]
        self._turn_on_backlight()
        self._tft = self._screen_setup()
        self._draw_borders()
        self._draw_static_upper_left()
        self._draw_static_upper_right()
        self._draw_static_middle()
        self._draw_static_bottom()

    def _draw_borders(self):
        # lines are drawn 1 pixel wide, so we need to run this width times
        for i in range(0, self._width):
            # border
            self._tft.rect(i, i, 240 - 2 * i, 240 - 2 * i, self._color)

            # horizontal divider between upper and middle
            self._tft.hline(self._width, 82 - int(self._width / 2) + i, 240 - 2 * self._width, self._color)

            # vertical divider between upper left and upper right
            self._tft.vline(120 - int(self._width / 2) + i, self._width, 82 - int(1.5 * self._width), self._color)

            # horizontal divider between middle and bottom
            self._tft.hline(self._width, 199 - int(self._width / 2) + i, 240 - 2 * self._width, self._color)

    def _draw_static_upper_left(self):
        # upper left bg_color
        self._tft.fill_rect(self._width, self._width, 120 - self._width - int(self._width / 2),
                            82 - int(1.5 * self._width), self._bg_color)
        self._tft.write(font_16, "Health%", 8 + 4, 14, self._color, self._bg_color)

    def draw_upper_left(self, health):
        self._tft.write(font_32, str(health), self._width + 18, 37, self._color, self._bg_color)

    def _draw_static_upper_right(self):
        pass

    def _draw_static_middle(self):
        # middle bg_color
        self._tft.fill_rect(self._width, 82 + int(self._width / 2), 240 - self._width * 2, 109, self._bg_color)
        self._tft.write(font_16, "Countdown", 8 + 50, 92, self._color, self._bg_color)

    def draw_middle(self, countdown_seconds):
        countdown = time.localtime(countdown_seconds)
        countdown_str = str(countdown[4]) + ":" + '{:0>2}'.format(countdown[5])
        self._tft.fill_rect(self._width, 121, 240 - self._width * 2, font_64.HEIGHT, self._bg_color)
        self._tft.write(font_64, countdown_str, self._width + 20, 121, self._color, self._bg_color)

    def _draw_static_bottom(self):
        # bottom bg_color
        self._tft.fill_rect(self._width, 199 + int(self._width / 2), 240 - self._width * 2, 29, self._bg_color)

    @staticmethod
    def _turn_on_backlight():
        i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
        imu = LIS2HH12(i2c, address=0x18, sf=SF_G)
        # enable the ACC interrupt to turn on backlight
        imu.enable_act_int()

    @staticmethod
    def _screen_setup():
        spi = SPI(2, baudrate=40000000, polarity=1)
        pcs = Pin(5, Pin.OUT)
        pdc = Pin(33, Pin.OUT)
        prst = Pin(32, Pin.OUT)

        tft = st7789.ST7789(
            spi,
            240,
            240,
            reset=prst,
            cs=pcs,
            dc=pdc)

        tft.init()
        tft.fill(st7789.BLACK)

        return tft


class DisplayPlayer(Display):
    """
        +---------+--------+
        | Health  | Ammo   |
        |  100%   | 100%   |
        +---------+--------+
        |    countdown     |
        |       0:00       |
        +------------------+
        |    player buzz   |
        +------------------+
        """
    def _draw_static_upper_right(self):
        # upper right bg_color
        self._tft.fill_rect(120 + int(self._width / 2), self._width, 120 - self._width - int(self._width / 2),
                            82 - int(1.5 * self._width), self._bg_color)
        self._tft.write(font_16, "Ammo%", 120 + 4 + 6, 14, self._color, self._bg_color)

    def draw_upper_right(self, ammo):
        self._tft.write(font_32, str(ammo), 120 + int(self._width / 2) + 18, 37, self._color, self._bg_color)

    def _draw_static_bottom(self):
        Display._draw_static_bottom(self)
        self._tft.write(font_16, "Player " + self._team, 8 + 50, 209, self._color, self._bg_color)


class DisplayFlag(Display):
    """
        +---------+--------+
        | Health  | blue   |
        |  100%   |        |
        +---------+--------+
        |    countdown     |
        |       0:00       |
        +------------------+
        |    flag buzz   |
        +------------------+
        """

    def _draw_static_upper_right(self):
        # upper right bg_color
        self._tft.fill_rect(120 + int(self._width / 2), self._width, 120 - self._width - int(self._width / 2),
                            82 - int(1.5 * self._width), self._color)

    def _draw_static_bottom(self):
        Display._draw_static_bottom(self)
        self._tft.write(font_16, "Flag " + self._team, 8 + 50, 209, self._color, self._bg_color)


def test_player_screens():
    for team in teams.teams:
        player_screen = DisplayPlayer(team)
        player_screen.draw_upper_left(100)
        player_screen.draw_upper_right(100)
        player_screen.draw_middle(5 * 60)

        time.sleep(1)


def test_flag_screens():
    for team in teams.teams:
        flag_screen = DisplayFlag(team)
        flag_screen.draw_upper_left(100)
        flag_screen.draw_middle(5 * 60)

        time.sleep(1)


test_player_screens()
test_flag_screens()
