files = [
    "src/booting_screen.py",
    "src/chango_16.py",
    "src/chango_32.py",
    "src/chango_64.py",
    "src/display.py",
    "src/effects.py",
    "src/fri3d_logo.py",
    "src/hardware.py",
    "src/main.py",
    "src/monitor_countdown.py",
    "src/monitor_ir.py",
    "src/mvp.py",
    "src/profiles_common.py",
    "src/profiles_mvp.py",
    "src/statemachine.py",
    "src/teams.py",
    "src/vga1_16x32.py",
    "Timeblaster/MicroPython/blaster.py"
]

freeze(".", files)
freeze("micropython-mqtt/mqtt_as", "mqtt_as.py")

