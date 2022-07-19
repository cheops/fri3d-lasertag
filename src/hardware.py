from machine import SoftI2C, Pin, SPI, TouchPad
from lis2hh12 import LIS2HH12, SF_G
from neopixel import NeoPixel
import st7789py as st7789
import gc

setup_ready = False


def _screen_setup():
    spi = SPI(2, baudrate=40000000, polarity=1)
    prst = Pin(32, Pin.OUT)
    pcs = Pin(5, Pin.OUT)
    pdc = Pin(33, Pin.OUT)

    gc.collect()  # Precaution before instantiating framebuffer

    screen = st7789.ST7789(
        spi=spi,
        width=240,
        height=240,
        reset=prst,
        cs=pcs,
        dc=pdc)

    screen.fill(st7789.BLACK)

    return screen


def _turn_on_backlight():
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
    imu = LIS2HH12(i2c, address=0x18, sf=SF_G)
    # enable the ACC interrupt to turn on backlight
    imu.enable_act_int()


def _neopixels_setup():
    pin = Pin(2, Pin.OUT)
    neopixels = NeoPixel(pin, 3)
    return neopixels


if not setup_ready:
    # _turn_on_backlight()

    # can be used as globals
    # import hardware
    # hardware.tft
    tft = _screen_setup()
    neopixels = _neopixels_setup()
    boot_button = Pin(0, Pin.IN)
    touch_0 = TouchPad(Pin(27))
    touch_1 = TouchPad(Pin(14))
    touch_2 = TouchPad(Pin(13))

    import blaster
    #result = blaster.blaster.start_chatter()
    #if not result:
    #    print('no blaster')
    #    blaster = None

    setup_ready = True


