#include <Arduino.h>

#include "mvp.hpp"
#include "ir_receive.hpp"
#include "ble_client.hpp"
#include "profile_mvp.hpp"


// multi core documentation https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/freertos-smp.html
// arduino esp32 documentation https://espressif-docs.readthedocs-hosted.com/projects/arduino-esp32/en/latest/
// arduino reference https://www.arduino.cc/reference/en/
// TimeBlaster https://github.com/area3001/Timeblaster

// to read https://microcontrollerslab.com/category/freertos-arduino-tutorial/

StateMachine mvp_statemachine = StateMachine(&FLAG_BUZZ_PROFILE, TRANSITIONS_MVP, TRANSITIONS_COUNT, &BOOTING);


int64_t startCountdownMicros = esp_timer_get_time();
int64_t lastMicrosCountdown = startCountdownMicros;
const uint32_t countdownInterval = 1000000; // 1 second
uint16_t playing_time = PLAYING_TIME;

int64_t startBlasterSendMicros = esp_timer_get_time();
int64_t lastMicrosBlasterSend = startBlasterSendMicros;
const uint32_t blasterSendInterval = 5000000; // 5 seconds
uint8_t team = eNoTeam;
uint8_t brightness = 0;
bool blaster_set_settings_supported = true;

void setup(void)
{
    Serial.begin(115200);
    delay(500);

    blasterLink.start_listen();

    badgeIrReceiver.setup();

    //bleClient.start_listen(eBleMessageTypePrestart);

    
}

void loop()
{
    mvp_statemachine.start();

    blasterLink.process_buffer();
    
    // process received blaster messages
    while (blasterLink.message_available()) {
        DataPacket message = blasterLink.pop_message();
        Serial.print("-Blaster_link: ");
        message.print(&Serial);
    }


    badgeIrReceiver.receive_ir_data();

    // process received ir messages
    while (badgeIrReceiver.message_available()) {
        DataPacket message = badgeIrReceiver.pop_message();
        Serial.print("-Ir_link: ");
        message.print(&Serial);
    }


    if (bleClient.listen_type_found()) {
        BleMessage ble_message = bleClient.get_ble_message();
        ble_message.print(&Serial);
        bleClient.reset();
    } else {
        if (!bleClient.is_listening()) {
            delay(1000);
            bleClient.start_listen(eBleMessageTypePrestart);
        }
    }


    /*
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
    */

    // update blaster settings
    startBlasterSendMicros = esp_timer_get_time();
    if (startBlasterSendMicros - lastMicrosBlasterSend >= blasterSendInterval)
    {
        lastMicrosBlasterSend = startBlasterSendMicros;

        bool success = blasterLink.set_channel(2);
        Serial.printf("Set channel: %x\n", success);

        if (blaster_set_settings_supported) { // only try set_settings once, needs blaster firmware update
            success = blasterLink.set_settings(true, brightness);
            Serial.printf("Set settings: %x\n", success);
            brightness += 1;
            if (brightness >= 8) brightness = 0;
            if (!success) blaster_set_settings_supported = false;
        }

        success = blasterLink.set_team(TeamColor(team));
        Serial.printf("Set team: %x\n", success);
        team += 1;
        if (team >= 16) team = 0;
    }
    
}