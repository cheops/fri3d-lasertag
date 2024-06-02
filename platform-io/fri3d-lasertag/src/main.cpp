#include <Arduino.h>

#include "mvp.hpp"
#include "profile_mvp.hpp"


// multi core documentation https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/freertos-smp.html
// arduino esp32 documentation https://espressif-docs.readthedocs-hosted.com/projects/arduino-esp32/en/latest/
// arduino reference https://www.arduino.cc/reference/en/
// TimeBlaster https://github.com/area3001/Timeblaster

// to read https://microcontrollerslab.com/category/freertos-arduino-tutorial/

/**
 *starting the statemachine in another task gives a crash when bleClient is accessed

void task_statemachine(void* pvParameter) {
    StateMachine* thiz = reinterpret_cast<StateMachine*>(pvParameter);

    // this keeps running forever
    thiz->start();

    log_e("our Statemachine has crashed.");

    vTaskDelete(NULL);
}
void setup(void)
{
    Serial.begin(115200);
    delay(500);

    TaskHandle_t* ptr_task_statemachine;
    const int taskCore = tskNO_AFFINITY;
    const int taskPriority = tskIDLE_PRIORITY;
    (
        task_statemachine,         //Function to implement the task 
        "task_statemachine",       //Name of the task
        5000,                      //Stack size in words 
        &mvp_statemachine,         //Task input parameter 
        taskPriority,              //Priority of the task 
        ptr_task_statemachine,     //Task handle.
        taskCore);                 //Core where the task should run
}
*/

void setup(void)
{
    Serial.begin(115200);

    {
        Badge2020_TFT tft;
        tft.enableBacklight();
    }

    delay(1000); // wait for blaster to start

    StateMachine mvp_statemachine = StateMachine(&PLAYER_GIGGLE_PROFILE, TRANSITIONS_MVP, TRANSITIONS_COUNT, &PRACTICING);
    mvp_statemachine.start();
    // void loop() is never reached, since statemachine keeps running forever
}

void loop()
{
    // nothing is done here
    log_d("terminating the loop task");
    vTaskDelete(NULL);
}