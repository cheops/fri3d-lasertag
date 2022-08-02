import st7789
import time

from teams import team_colors, teams
from hardware import tft

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

    _width = 8
    _bg_color = st7789.WHITE

    def __init__(self, team):
        self._team = team
        self._color = team_colors[self._team]
        self._prev_upper_left_len_pixels = 0
        self._prev_middle_len_pixels = 0

    def draw_initial(self):
        self._draw_borders()
        self._draw_static_upper_left()
        self._draw_static_upper_right()
        self._draw_static_bottom()

    def _draw_borders(self):
        # lines are drawn 1 pixel wide, so we need to run this width times
        for i in range(0, self._width):
            # border
            tft.rect(i, i, 240 - 2 * i, 240 - 2 * i, self._color)

            # horizontal divider between upper and middle
            tft.hline(self._width, 82 - int(self._width / 2) + i, 240 - 2 * self._width, self._color)

            # vertical divider between upper left and upper right
            tft.vline(120 - int(self._width / 2) + i, self._width, 82 - int(1.5 * self._width), self._color)

            # horizontal divider between middle and bottom
            tft.hline(self._width, 199 - int(self._width / 2) + i, 240 - 2 * self._width, self._color)

    def _draw_static_upper_left(self):
        # upper left bg_color
        tft.fill_rect(self._width, self._width, 120 - self._width - int(self._width / 2),
                      82 - int(1.5 * self._width), self._bg_color)
        tft.write(font_16, "Health%", 8 + 4, 14, self._color, self._bg_color)

    def draw_upper_left(self, health):
        health_str = str(health)
        tft.write(font_32, str(health), self._width + 18, 37, self._color, self._bg_color)
        upper_left_len_pixels = tft.write_len(font_32, health_str)
        diff = self._prev_upper_left_len_pixels - upper_left_len_pixels
        if diff > 0:
            tft.fill_rect(self._width + 18 + upper_left_len_pixels, 37, diff, font_32.HEIGHT, self._bg_color)
        self._prev_upper_left_len_pixels = upper_left_len_pixels

    def _draw_static_upper_right(self):
        pass

    def draw_static_middle(self, txt):
        # middle bg_color
        tft.fill_rect(self._width, 82 + int(self._width / 2), 240 - self._width * 2, 109, self._bg_color)
        tft.write(font_16, txt, 8 + 50, 92, self._color, self._bg_color)

    def draw_middle(self, countdown_seconds):
        countdown = time.localtime(countdown_seconds)
        countdown_str = str(countdown[4]) + ":" + '{:0>2}'.format(countdown[5])
        tft.write(font_64, countdown_str, self._width + 20, 121, self._color, self._bg_color)
        middle_len_pixels = tft.write_len(font_64, countdown_str)
        diff = self._prev_middle_len_pixels - middle_len_pixels
        if diff > 0:
            tft.fill_rect(self._width + 20 + middle_len_pixels, 121, diff, font_64.HEIGHT, self._bg_color)
        self._prev_middle_len_pixels = middle_len_pixels

    def _draw_static_bottom(self):
        # bottom bg_color
        tft.fill_rect(self._width, 199 + int(self._width / 2), 240 - self._width * 2, 29, self._bg_color)


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
        tft.fill_rect(120 + int(self._width / 2), self._width, 120 - self._width - int(self._width / 2),
                      82 - int(1.5 * self._width), self._bg_color)
        tft.write(font_16, "Ammo%", 120 + 4 + 6, 14, self._color, self._bg_color)

    def draw_upper_right(self, ammo):
        pixel_length = tft.write_len(font_16, str(ammo))
        tft.write(font_32, str(ammo), 120 + int(self._width / 2) + 18, 37, self._color, self._bg_color)

    def _draw_static_bottom(self):
        Display._draw_static_bottom(self)
        tft.write(font_16, "Player " + self._team, 8 + 50, 209, self._color, self._bg_color)


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
        tft.fill_rect(120 + int(self._width / 2), self._width, 120 - self._width - int(self._width / 2),
                      82 - int(1.5 * self._width), self._color)

    def _draw_static_bottom(self):
        Display._draw_static_bottom(self)
        tft.write(font_16, "Flag " + self._team, 8 + 50, 209, self._color, self._bg_color)


def test_player_screens():
    for team in teams.teams:
        player_screen = DisplayPlayer(team)
        player_screen.draw_upper_left(100)
        player_screen.draw_upper_right(100)
        player_screen.draw_static_middle("Playing")
        player_screen.draw_middle(5 * 60)

        time.sleep(1)


def test_flag_screens():
    for team in teams.teams:
        flag_screen = DisplayFlag(team)
        flag_screen.draw_upper_left(100)
        flag_screen.draw_static_middle("Hiding")
        flag_screen.draw_middle(5 * 60)

        time.sleep(1)

# test_player_screens()
# test_flag_screens()
