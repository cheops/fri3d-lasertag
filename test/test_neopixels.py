from neopixel import NeoPixel
from time import sleep, sleep_ms
from machine import Pin

NUM_LEDS = 5
LED_PIN = 2

neopixel_pin = Pin(LED_PIN, Pin.OUT)
np = NeoPixel(neopixel_pin, NUM_LEDS)


def set_color(r, g, b):
    for i in range(NUM_LEDS):
        np[i] = (r, g, b)
    np.write()


def bounce(r, g, b, wait):
    for i in range(2 * NUM_LEDS):
        for j in range(NUM_LEDS):
            np[j] = (r, g, b)
        if (i // NUM_LEDS) % 2 == 0:
            np[i % NUM_LEDS] = (0, 0, 0)
        else:
            np[NUM_LEDS - 1 - (i % NUM_LEDS)] = (0, 0, 0)
        np.write()
        sleep_ms(wait)


# cycle
def cycle(r, g, b, wait):
    for i in range(NUM_LEDS):
        for j in range(NUM_LEDS):
            np[j] = (0, 0, 0)
        np[i % NUM_LEDS] = (r, g, b)
        np.write()
        sleep_ms(wait)


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




# rainbow
def rainbow_cycle(wait):
    brightness = 20
    for j in range(255):
        for i in range(NUM_LEDS):
            rc_index = (i * 256 // NUM_LEDS) + j
            np[i] = wheel(rc_index & 255, brightness)
        np.write()
        sleep_ms(wait)


# turn off all pixels
def clear():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
        np.write()


def draw_rainbow(duration):
    for t in range(duration, 0, -1):
        rainbow_cycle(int(t/100))

def flash(r, g, b, wait, count):
    for i in range(0, count):
        set_color(r, g, b)
        sleep_ms(wait)
        set_color(0,0,0)
        sleep_ms(wait)

clear()

#draw_rainbow(10)

flash(255, 255, 2555, 30, 5)

clear()
