from neopixel import NeoPixel
from time import sleep, sleep_ms
import gc
import _thread
import uasyncio
from machine import Pin, SPI, PWM

import fri3d_logo
import vga1_16x32 as font_32


try:
    import st7789
    compiled_disp_lib = True
except ImportError as e1:
    try:
        import st7789py as st7789
        compiled_disp_lib = False
    except ImportError:
        print('missing display library st7789 or st7789py')
        raise e1

spi = SPI(2, baudrate=40000000, polarity=1)
prst = Pin(32, Pin.OUT)
pcs = Pin(5, Pin.OUT)
pdc = Pin(33, Pin.OUT)

gc.collect()  # Precaution before instantiating framebuffer

if compiled_disp_lib:
    screen = st7789.ST7789(
        spi=spi,
        width=240,
        height=240,
        reset=prst,
        cs=pcs,
        dc=pdc,
        buffer_size=240 * 240 * 2)
    sleep(0.2)
    screen.init()
else:
    screen = st7789.ST7789(
        spi=spi,
        width=240,
        height=240,
        reset=prst,
        cs=pcs,
        dc=pdc)

#screen.fill(st7789.RED)
#sleep(0.2)
#screen.fill(st7789.GREEN)
#sleep(0.2)
#screen.fill(st7789.BLUE)
#sleep(0.2)
screen.fill(st7789.BLACK)


NUM_LEDS = 5
LED_PIN = 2

neopixel_pin = Pin(LED_PIN, Pin.OUT)
np = NeoPixel(neopixel_pin, NUM_LEDS)


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

buzzer_pin = Pin(32, Pin.OUT)

def BuzzerR2D2(pin):
  R2D2_NOTES = [3520, 3135.96, 2637.02, 2093, 2349.32, 3951.07, 2793.83, 4186.01, 3520, 3135.96, 2637.02, 2093, 2349.32, 3951.07, 2793.83, 4186.01]
  R2D2_DURATION = [80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80]
  R2D2_SLEEP = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
  play(pin, R2D2_NOTES, R2D2_DURATION, R2D2_SLEEP)

async def draw_fri3d_logo(duration):
    # blink the logo and the text, faster and faster
    row = 3
    for t in range(duration, 0, -2):
        screen.fill(st7789.BLACK)
        screen.text(font_32, 'fri3d-lasertag', 0, row * font_32.HEIGHT)
        await uasyncio.sleep(t / 100)
        screen.fill_rect(0, row * font_32.HEIGHT, 240, font_32.HEIGHT, st7789.BLACK)
        screen.bitmap(fri3d_logo, 0, 0)
        await uasyncio.sleep(t / 100)
    screen.text(font_32, 'fri3d-lasertag', 0, row * font_32.HEIGHT)


# function to go through all colors
def wheel(pos, max):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (int(max - pos * 3 * max / 255), int(pos * 3 * max / 255), 0)
    if pos < 170:
        pos -= 85
        return (0, int(max - pos * 3 * max / 255), int(pos * 3 * max / 255))
    pos -= 170
    return (int(pos * 3 * max / 255), 0, int(max - pos * 3 * max / 255))


brightness = 20


# rainbow
async def rainbow_cycle(wait):
    for j in range(255):
        for i in range(NUM_LEDS):
            rc_index = (i * 256 // NUM_LEDS) + j
            np[i] = wheel(rc_index & 255, brightness)
        np.write()
        await uasyncio.sleep_ms(wait)

async def draw_rainbow(duration):
    for t in range(duration, 0, -1):
        await rainbow_cycle(0)

def set_color(r, g, b):
    for i in range(NUM_LEDS):
        np[i] = (r, g, b)
    np.write()

# turn off all pixels
def clear():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()

music = _thread.start_new_thread(BuzzerR2D2, (buzzer_pin,))
logo = uasyncio.create_task(draw_fri3d_logo(10))
#uasyncio.run(draw_fri3d_logo(10))
#draw_fri3d_logo(10)
#draw_rainbow(10)
pixels = uasyncio.run(draw_rainbow(2))
#pixels = _thread.start_new_thread(draw_rainbow, (10,))

sleep(1)

screen.fill(st7789.BLACK)
clear()
sleep(1)

music = _thread.start_new_thread(BuzzerStarWars, (buzzer_pin,))
logo = uasyncio.create_task(draw_fri3d_logo(30))
pixels = uasyncio.run(draw_rainbow(8))
#pixels = _thread.start_new_thread(draw_rainbow, (30,))
#logo = _thread.start_new_thread(draw_fri3d_logo, (30,))
sleep(1)

clear()
screen.fill(st7789.BLACK)
