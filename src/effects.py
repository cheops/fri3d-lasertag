from time import sleep, sleep_ms
import _thread
import uasyncio
import gc
from machine import PWM

import fri3d_logo
import vga1_16x32 as font_32

from hardware import neopixels_5, tft, buzzer_pin
import st7789


def screen_cycle_rgb():
    tft.fill(st7789.RED)
    sleep_ms(200)
    tft.fill(st7789.GREEN)
    sleep_ms(200)
    tft.fill(st7789.BLUE)
    sleep_ms(200)
    tft.fill(st7789.BLACK)


def play(buz_pin, sw_notes, sw_duration, sw_sleep, active_duty=50):
    buz = PWM(buz_pin)
    for i, note in enumerate(sw_notes):
        buz.freq(int(note))
        buz.duty(active_duty)
        sleep_ms(sw_duration[i])
        buz.duty(0)
        sleep_ms(sw_sleep[i])
    buz.duty(0)
    buz.deinit()


def BuzzerStarWars(pin):
    SW_NOTES = [293.66, 293.66, 293.66, 392.0, 622.25, 554.37, 523.25, 454, 932.32, 622.25, 554.37, 523.25, 454, 932.32, 622.25, 554.37, 523.25, 554.37, 454]
    SW_DURATION = [180, 180, 180, 800, 800, 180, 180, 180, 800, 400, 180, 180, 180, 800, 400, 180, 180, 180, 1000]
    SW_SLEEP = [40, 40, 40, 100, 100, 40, 40, 40, 100, 50, 40, 40, 40, 100, 50, 40, 40, 40, 100]
    play(pin, SW_NOTES, SW_DURATION, SW_SLEEP)


def BuzzerR2D2(pin):
    R2D2_NOTES = [3520, 3135.96, 2637.02, 2093, 2349.32, 3951.07, 2793.83, 4186.01, 3520, 3135.96, 2637.02, 2093, 2349.32, 3951.07, 2793.83, 4186.01]
    R2D2_DURATION = [80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80]
    R2D2_SLEEP = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
    play(pin, R2D2_NOTES, R2D2_DURATION, R2D2_SLEEP)

async def draw_fri3d_logo(duration):
    # blink the logo and the text, faster and faster
    row = 3
    for t in range(duration, 0, -2):
        tft.fill(st7789.BLACK)
        tft.text(font_32, 'fri3d-lasertag', 0, row * font_32.HEIGHT)
        await uasyncio.sleep(t / 100)
        tft.fill_rect(0, row * font_32.HEIGHT, 240, font_32.HEIGHT, st7789.BLACK)
        tft.bitmap(fri3d_logo, 0, 0)
        await uasyncio.sleep(t / 100)
    tft.text(font_32, 'fri3d-lasertag', 0, row * font_32.HEIGHT)


# function to go through all colors
def wheel(pos, max_brightness):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (int(max_brightness - pos * 3 * max_brightness / 255), int(pos * 3 * max_brightness / 255), 0)
    if pos < 170:
        pos -= 85
        return (0, int(max_brightness - pos * 3 * max_brightness / 255), int(pos * 3 * max_brightness / 255))
    pos -= 170
    return (int(pos * 3 * max_brightness / 255), 0, int(max_brightness - pos * 3 * max_brightness / 255))


brightness = 20
NUM_LEDS = 5

# rainbow
async def rainbow_cycle(wait):
    for j in range(255):
        for i in range(NUM_LEDS):
            rc_index = (i * 256 // NUM_LEDS) + j
            neopixels_5[i] = wheel(rc_index & 255, brightness)
        neopixels_5.write()
        await uasyncio.sleep_ms(wait)


async def draw_rainbow(duration):
    for t in range(duration, 0, -1):
        await rainbow_cycle(0)


def set_color(r, g, b):
    for i in range(NUM_LEDS):
        neopixels_5[i] = (r, g, b)
    neopixels_5.write()


# turn off all pixels
def clear():
    for i in range(NUM_LEDS):
        neopixels_5[i] = (0, 0, 0)
    neopixels_5.write()


def effect_R2D2():
    _thread.start_new_thread(BuzzerR2D2, (buzzer_pin,))
    uasyncio.create_task(draw_fri3d_logo(10))
    uasyncio.run(draw_rainbow(2))


def effect_star_wars():
    _thread.start_new_thread(BuzzerStarWars, (buzzer_pin,))
    uasyncio.create_task(draw_fri3d_logo(30))
    uasyncio.run(draw_rainbow(8))


def effect_clean():
    tft.fill(st7789.BLACK)
    clear()
    gc.collect()