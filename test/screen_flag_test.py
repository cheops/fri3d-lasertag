import time
import gc
from machine import Pin, SPI

import st7789

import chango_16 as font_16
import chango_32 as font_32
import chango_64 as font_64

spi = SPI(2, baudrate=40000000, polarity=1)
pcs = Pin(5, Pin.OUT)
pdc = Pin(33, Pin.OUT)

gc.collect()  # Precaution before instantiating framebuffer

tft = st7789.ST7789(
    spi=spi,
    width=240,
    height=240,
    cs=pcs,
    dc=pdc,
    buffer_size=240 * 240 * 2)
tft.init()

prev_middle_len_pixels = 0


def draw_borders(width, color, bg_color):
    for i in range(0, width):
        # border
        tft.rect(i, i, 240 - 2 * i, 240 - 2 * i, color)

        # horizontal line
        tft.hline(width, 82 - int(width / 2) + i, 240 - 2 * width, color)

        tft.vline(120 - int(width / 2) + i, width, 82 - int(1.5 * width), color)

        # horizontal line
        tft.hline(width, 199 - int(width / 2) + i, 240 - 2 * width, color)

    # upper left bg_color
    tft.fill_rect(width, width, 120 - width - int(width / 2), 82 - int(1.5 * width), bg_color)
    tft.write(font_16, "Health%", 8 + 4, 14, color, bg_color)

    # upper right color
    tft.fill_rect(120 + int(width / 2), width, 120 - width - int(width / 2), 82 - int(1.5 * width), color)

    # middle bg_color
    tft.fill_rect(width, 82 + int(width / 2), 240 - width * 2, 109, bg_color)
    tft.write(font_16, "Countdown", 8 + 50, 92, color, bg_color)

    # bottom bg_color
    tft.fill_rect(width, 199 + int(width / 2), 240 - width * 2, 29, bg_color)
    tft.write(font_16, "Flag Giggle", 8 + 50, 209, color, bg_color)


def draw_health(health, border_width, color, bg_color):
    tft.write(font_32, str(health), border_width + 18, 37, color, bg_color)


def draw_middle(countdown_seconds):
    global prev_middle_len_pixels
    width = 8
    countdown = time.localtime(countdown_seconds)
    countdown_str = str(countdown[4]) + ":" + '{:0>2}'.format(countdown[5])
    tft.write(font_64, countdown_str, width + 20, 121, color, bg_color)
    middle_len_pixels = tft.write_len(font_64, countdown_str)
    diff = prev_middle_len_pixels - middle_len_pixels
    if diff > 0:
        tft.fill_rect(width + 20 + middle_len_pixels, 121, diff, font_64.HEIGHT, bg_color)
    prev_middle_len_pixels = middle_len_pixels


def draw_countdown(countdown_seconds, border_width, color, bg_color):
    countdown = time.localtime(countdown_seconds)
    countdown_str = str(countdown[4]) + ":" + '{:0>2}'.format(countdown[5])
    tft.fill_rect(border_width, 121, 240 - border_width * 2, font_64.HEIGHT, bg_color)
    tft.write(font_64, countdown_str, border_width + 20, 121, color, bg_color)


color_rex = st7789.color565(255, 0, 0)
color_giggle = st7789.color565(0, 140, 0)
color_buzz = st7789.color565(0, 0, 210)

tft.fill(st7789.BLACK)
border_width = 8
color = color_buzz
bg_color = st7789.WHITE
health = 100
ammo = 100
countdown_seconds = 5 * 60

draw_borders(border_width, color, bg_color)

draw_health(health, border_width, color, bg_color)
draw_countdown(countdown_seconds, border_width, color, bg_color)


def simulation(countdown_seconds):
    for i in range(countdown_seconds, 0, -1):
        time.sleep(0.3)
        countdown_seconds -= 1
        #draw_countdown(countdown_seconds, border_width, color, bg_color)
        draw_middle(countdown_seconds)
        print(countdown_seconds)

    while True:
        tft.write(font_64, "0:00", border_width + 20, 121, color, bg_color)
        time.sleep(1)
        tft.fill_rect(border_width, 121, 240 - border_width * 2, font_64.HEIGHT, bg_color)
        time.sleep(1)


simulation(countdown_seconds)
