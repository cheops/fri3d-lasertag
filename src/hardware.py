from machine import SoftI2C, Pin, SPI, TouchPad
from lis2hh12 import LIS2HH12, SF_G
from neopixel import NeoPixel
import gc
import st7789

setup_ready = False


def _screen_setup():
    spi = SPI(2, baudrate=40000000, polarity=1)
    pcs = Pin(5, Pin.OUT)
    pdc = Pin(33, Pin.OUT)

    gc.collect()  # Precaution before instantiating framebuffer

    screen = st7789.ST7789(
        spi=spi,
        width=240,
        height=240,
        cs=pcs,
        dc=pdc,
        buffer_size=240 * 240 * 2)
    screen.init()

    return screen


def _turn_on_backlight():
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
    imu = LIS2HH12(i2c, address=0x18, sf=SF_G)
    # enable the ACC interrupt to turn on backlight
    imu.enable_act_int()


def _neopixels_setup(amount):
    pin = Pin(2, Pin.OUT)
    neopixels = NeoPixel(pin, amount)
    return neopixels


if not setup_ready:
    _turn_on_backlight()

    # can be used as globals
    # import hardware
    # hardware.tft
    tft = _screen_setup()

    neopixels_3 = _neopixels_setup(3)
    neopixels_5 = _neopixels_setup(5)

    boot_button = Pin(0, Pin.IN)

    touch_0 = TouchPad(Pin(27))
    touch_1 = TouchPad(Pin(14))
    touch_2 = TouchPad(Pin(13))

    buzzer_pin = Pin(32, Pin.OUT)

    import blaster
    #result = blaster.blaster.start_chatter()
    #if not result:
    #    print('no blaster')
    #    blaster = None

    setup_ready = True


