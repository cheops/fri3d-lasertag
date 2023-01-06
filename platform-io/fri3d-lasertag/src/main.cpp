#include <Arduino.h>

#include "mvp.hpp"
#include "blaster_link.hpp"
#include "ir_receive.hpp"

// multi core documentation https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/freertos-smp.html
// arduino esp32 documentation https://espressif-docs.readthedocs-hosted.com/projects/arduino-esp32/en/latest/
// arduino reference https://www.arduino.cc/reference/en/
// TimeBlaster https://github.com/area3001/Timeblaster

// to read https://microcontrollerslab.com/category/freertos-arduino-tutorial/

int64_t startCountdownMicros = esp_timer_get_time();
int64_t lastMicrosCountdown = startCountdownMicros;
const uint32_t countdownInterval = 1000000; // 1 second
uint16_t playing_time = PLAYING_TIME;

int64_t startBadgeSendMicros = esp_timer_get_time();
int64_t lastMicrosBadgeSend = startBadgeSendMicros;
const uint32_t badgeSendInterval = 5000000; // 5 seconds
uint8_t team = eNoTeam;

void setup(void)
{
    Serial.begin(115200);

    display.init();

    display.draw_upper_left(100);
    display.draw_upper_right(100);
    display.draw_static_middle("Playing");

    blasterLink.start_listen();

    badgeIrReceiver.setup();
}

void loop()
{

    blasterLink.process_buffer();
    badgeIrReceiver.receive_ir_data();

    startCountdownMicros = esp_timer_get_time();
    if (startCountdownMicros - lastMicrosCountdown >= countdownInterval)
    {
        int64_t elapsed_sec = (startCountdownMicros - lastMicrosCountdown) / 1000000;
        lastMicrosCountdown = startCountdownMicros;
        playing_time -= elapsed_sec;
        if (playing_time > PLAYING_TIME)
        { 
            // uint16_t rollover
            playing_time = PLAYING_TIME;
        }

        // Serial.println(playing_time);

        display.draw_middle(playing_time);
    }

    // set the IR channel
    startBadgeSendMicros = esp_timer_get_time();
    if (startBadgeSendMicros - lastMicrosBadgeSend >= badgeSendInterval)
    {
        lastMicrosBadgeSend = startBadgeSendMicros;

        bool success = blasterLink.set_channel(2);
        Serial.printf("Set channel: %x\n", success);

        success = blasterLink.set_team(TeamColor(team));
        Serial.printf("Set team: %x\n", success);
        team += 1;
        if (team >= 16) {
            team = 0;
        }
    }
}