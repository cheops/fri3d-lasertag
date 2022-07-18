import time
import uasyncio


async def monitor_countdown(countdown_seconds, handle_countdown_end, update_countdown_display):
    start = time.ticks_ms()  # get millisecond counter
    previous_remaining_seconds = None
    while True:
        uasyncio.sleep(100)
        delta = time.ticks_diff(time.ticks_ms(), start)  # compute time difference

        remaining_seconds = int((countdown_seconds * 1000 - delta) / 1000)
        if remaining_seconds != previous_remaining_seconds:
            previous_remaining_seconds = remaining_seconds
            update_countdown_display(remaining_seconds)
        if delta >= countdown_seconds * 1000:
            handle_countdown_end()
            break

