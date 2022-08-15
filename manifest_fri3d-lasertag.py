files = [
    "ble_advertising.py",
    "booting_screen.py",
    "chango_16.py",
    "chango_32.py",
    "chango_64.py",
    "display.py",
    "effects.py",
    "fri3d_logo.py",
    "hardware.py",
    "main.py",
    "monitor_ble.py",
    "monitor_countdown.py",
    "monitor_ir.py",
    "monitor_mqtt.py",
    "mvp.py",
    "profiles_common.py",
    "profiles_mvp.py",
    "statemachine.py",
    "teams.py",
    "vga1_16x32.py",
]

freeze("src", files)
freeze("Timeblaster/MicroPython", "blaster.py")
freeze("micropython-mqtt/mqtt_as", "mqtt_as.py")

