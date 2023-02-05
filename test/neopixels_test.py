from time import sleep

from machine import Pin
from neopixel import NeoPixel

neopixel_pin = Pin(2, Pin.OUT)
neopixels = NeoPixel(neopixel_pin, 5)

print("testing neopixels")
max_brightness = 125
leds = 5
for i in range(0, max_brightness):
    neopixels[0] = (i, i, i)
    neopixels.write()
    sleep(0.003)
for p in range(0, leds - 1):
    for i in range(0, max_brightness):
        v = max_brightness - i
        neopixels[p] = (v, v, v)
        neopixels[p + 1] = (i, i, i)
        neopixels.write()
        sleep(0.003)
for i in range(0, max_brightness):
    v = max_brightness - i
    neopixels[leds - 1] = (v, v, v)
    neopixels.write()
    sleep(0.003)

neopixels[0] = (255, 0, 0)
neopixels[1] = (0, 0, 0)
neopixels[2] = (0, 0, 0)
neopixels[3] = (0, 0, 0)
neopixels[4] = (0, 0, 0)
neopixels.write()
sleep(0.3)
neopixels[0] = (0, 0, 0)
neopixels.write()
