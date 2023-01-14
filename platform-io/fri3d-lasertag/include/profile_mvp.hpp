
#ifndef PROFILE_MVP_HPP
#define PROFILE_MVP_HPP

#include <Badge2020_Buzzer.h>

#include "profile.hpp"
#include "statemachine.hpp"
#include "team.hpp"
#include "mvp.hpp"
#include "ble_client.hpp"
#include "blaster_link.hpp"
#include "ir_receive.hpp"
#include <Adafruit_NeoPixel.h>

#define LED_PIN    2
#define LED_COUNT  5

const char* flag_type_name = "Flag";
const char* player_type_name = "Player";

const int taskCore = tskNO_AFFINITY;
const int taskPriority = tskIDLE_PRIORITY;

class FlagAndPlayer : public Profile, public Model {
public:
    FlagAndPlayer(const Team team, Display* df) : Profile(), Model(), m_display(df), m_team(team) {
        Serial.printf("Create FlagAndPlayer Model %s\n", team.name().c_str());
    }

    Event* run(State* ptr_state) override {
        Serial.printf("FlagAndPlayer::run state:%s\n", ptr_state->m_name.c_str());
        m_ptr_state = ptr_state;

        m_display->draw_static_middle(m_ptr_state->m_name);

        if (m_ptr_state->equals(&BOOTING)) booting();
        else if (m_ptr_state->equals(&PRACTICING)) practicing();
        else if (m_ptr_state->equals(&HIDING)) hiding();
        else if (m_ptr_state->equals(&PLAYING)) playing();
        else if (m_ptr_state->equals(&FINISHING)) finishing();

        // wait for some task to set the event
        while(!has_event()) {
            //Serial.println("no event -> sleeping");
            vTaskDelay(100/portTICK_PERIOD_MS);
        }

        stop_tasks();

        return Model::run(m_ptr_state);
    }

    void add_task(TaskHandle_t* ptr_task_handle) {
        if (m_task_next_free_handle >= task_max_handles) {
            Serial.printf("FlagAndPlayer::add_task Error, reached task_max_handles: %d\n", task_max_handles);
        } else {
            m_task_handles[m_task_next_free_handle] = ptr_task_handle;
            m_task_next_free_handle += 1;
        }
    }

    void stop_tasks() {
        Serial.println("event has been set, notifying tasks to stop");
        if (m_task_next_free_handle > 0) {
            for (uint8_t i = 0; i < m_task_next_free_handle; i++) {
                Serial.printf("notify task: %d\n", i);
                if (m_task_handles[i] != NULL) {
                    BaseType_t xResult;
                    xResult = xTaskNotifyGive( m_task_handles[i]);
                    if ( xResult == pdFAIL) {
                        // failed to notify the task, 
                        Serial.printf("Failed notifying task with STOP_BIT, killing it. index: %d\n", i);
                        vTaskDelete(m_task_handles[i]);
                    }
                }
            }
            vTaskDelay(500 / portTICK_PERIOD_MS);
            m_task_next_free_handle = 0;
        }
    }

protected:
    const char* type_name;
    const Team m_team;

    Display* m_display;
    State* m_ptr_state;

    uint8_t m_health;
    int64_t m_last_hit_time;

    uint16_t m_hiding_time = HIDING_TIME;
    uint16_t m_playing_time = PLAYING_TIME;
    uint8_t m_hit_damage = HIT_DAMAGE;
    uint8_t m_hit_timeout = HIT_TIMEOUT;
    uint16_t m_current_playing_time = PLAYING_TIME;
    uint8_t m_shot_ammo = SHOT_AMMO;
    uint8_t m_practicing_channel = PRACTICING_CHANNEL;
    uint8_t m_playing_channel = PLAYING_CHANNEL;
    uint32_t m_mqtt_game_id;
    bool m_mqtt_during_playing;
    
    static const uint8_t task_max_handles = 10;
    uint8_t m_task_next_free_handle = 0;
    TaskHandle_t* m_task_handles[task_max_handles];

    void booting() {
        Serial.println("FlagAndPlayer::booting");
        
        // fetch all registered profiles and select a random one as the new StateMachineModel
        std::vector<Profile*> profiles = Profile::find_profiles();
        uint8_t rnd_index = random(profiles.size());
        Profile* ptr_new_profile = profiles[rnd_index];
        
        FlagAndPlayer* ptr_fap = reinterpret_cast<FlagAndPlayer*>(ptr_new_profile);
        Serial.printf("Selected %s %s\n", ptr_fap->type_name, ptr_fap->m_team.name().c_str());

        // not really needed, start of practicing will start with the new Model, and the FlagAndPlayer::m_team will be set correctly
        const Team new_team = ptr_fap->m_team;
        blasterLink.set_team(new_team.team_color());
        
        // set the new Model on the Event, so that a Model swich happens in the StateMachine
        Model* ptr_new_model = reinterpret_cast<Model*>(ptr_new_profile);
        CONFIRM_PROFILE.set_new_model(ptr_new_model);
        set_event(&CONFIRM_PROFILE);
    }

    virtual void practicing() {
        Serial.println("FlagAndPlayer::practicing");
        blasterLink.set_team(m_team.team_color());
        blasterLink.set_channel(m_practicing_channel);

        m_display->draw_static_middle(m_ptr_state->m_name);
        m_health = 100;
        m_display->draw_upper_left(m_health);

        
        TaskHandle_t* ptr_task_ble_handle;
        xTaskCreatePinnedToCore(
            this->task_ble_listen,     //Function to implement the task 
            "task_ble_listen",         //Name of the task
            5000,                      //Stack size in words 
            this,                      //Task input parameter 
            taskPriority,              //Priority of the task 
            ptr_task_ble_handle,       //Task handle.
            taskCore);                 //Core where the task should run

        add_task(ptr_task_ble_handle);
        
    }

    void hiding() {
        Serial.println("FlagAndPlayer::hiding");
        blasterLink.set_trigger_action(false, false, false, true); // disable trigger

        TaskHandle_t* ptr_task_countdown_handle;
        xTaskCreatePinnedToCore(
            this->task_countdown,      //Function to implement the task 
            "task_countdown",          //Name of the task
            5000,                      //Stack size in words 
            this,                      //Task input parameter 
            taskPriority,              //Priority of the task 
            ptr_task_countdown_handle, //Task handle.
            taskCore);                 //Core where the task should run

        add_task(ptr_task_countdown_handle);
    }

    virtual void playing() {
        Serial.println("FlagAndPlayer::_playing");
        blasterLink.set_channel(m_playing_channel);

        // playing loop
        TaskHandle_t* ptr_task_countdown_handle;
        xTaskCreatePinnedToCore(
            this->task_countdown,      //Function to implement the task 
            "task_countdown",          //Name of the task
            5000,                      //Stack size in words 
            this,                      //Task input parameter 
            taskPriority,              //Priority of the task 
            ptr_task_countdown_handle, //Task handle.
            taskCore);                 //Core where the task should run

        add_task(ptr_task_countdown_handle);
    }

    void finishing() {
        Serial.println("FlagAndPlayer::_finishing");
        blasterLink.set_channel(INVALID_CHANNEL);
        blasterLink.set_trigger_action(false, false, false, true); // disable trigger

        m_display->draw_middle(m_current_playing_time);

        TaskHandle_t* ptr_task_ble_handle;
        xTaskCreatePinnedToCore(
            this->task_ble_listen,     //Function to implement the task 
            "task_ble_listen",         //Name of the task
            5000,                      //Stack size in words 
            this,                      //Task input parameter 
            taskPriority,              //Priority of the task 
            ptr_task_ble_handle,       //Task handle.
            taskCore);                 //Core where the task should run

        add_task(ptr_task_ble_handle);
    }

    static void task_ble_listen(void* pvParameter) {
        Serial.println(":: task_ble_listen :: started.");
        FlagAndPlayer* thiz = reinterpret_cast<FlagAndPlayer*>(pvParameter);

        BleMessageType to_listen;
        Event* ptr_event;
        if (thiz->m_ptr_state->equals(&PRACTICING)) {
            to_listen = eBleMessageTypePrestart;
            ptr_event = &PRESTART;
        } else if (thiz->m_ptr_state->equals(&FINISHING)) {
            to_listen = eBleMessageTypeNextRound;
            ptr_event = &NEXT_ROUND;
        } else {
            Serial.printf("task_ble_listen :: nothing to listen for in state %s\n", thiz->m_ptr_state->m_name.c_str());
            vTaskDelete(NULL);
        }
        Serial.printf(":: task_ble_listen :: listening for:%d\n", to_listen);

        bleClient.start_listen(to_listen);
        
        TickType_t xMaxBlockTime = pdMS_TO_TICKS( 100 );
        bool should_stop = false;
        while(!should_stop) {
            if (bleClient.listen_type_found()) {
                BleMessage ble_message = bleClient.get_ble_message();
                bleClient.stop_listen();

                thiz->m_hiding_time = ble_message.get_hiding_time();
                thiz->m_playing_time = ble_message.get_playing_time();
                thiz->m_hit_damage = ble_message.get_hit_damage();
                thiz->m_hit_timeout = ble_message.get_hit_timeout();
                thiz->m_shot_ammo = ble_message.get_shot_ammo();
                thiz->m_practicing_channel = ble_message.get_practicing_channel();
                thiz->m_playing_channel = ble_message.get_playing_channel();
                thiz->m_mqtt_game_id = ble_message.get_mqtt_game_id();
                thiz->m_mqtt_during_playing = ble_message.get_mqtt_during_playing();

                // TODO the ble_message has funny values for shot_ammo
                ble_message.print(&Serial);

                Serial.printf("Setting event %s\n", ptr_event->m_name.c_str());
                thiz->set_event(ptr_event);

                xMaxBlockTime = portMAX_DELAY; // wait forever to get notified
            }

            // check if notified
            BaseType_t xResult;
            xResult = ulTaskNotifyTake(pdTRUE, xMaxBlockTime);  /* pdTRUE = clear bits on entry. */
            if ( xResult == pdPASS ) {
                Serial.println(":: task_ble_listen we got notified to stop, killing ourselves.");
                should_stop = true;
            }

        }// while(should_stop)

        bleClient.stop_listen();

        vTaskDelay(200/portTICK_PERIOD_MS);
        vTaskDelete(NULL);

    } // task_ble_listen

    static void task_countdown(void* pvParameter) {
        FlagAndPlayer* thiz = reinterpret_cast<FlagAndPlayer*>(pvParameter);
        int64_t start_time = esp_timer_get_time();

        uint16_t current_display_time;
        uint16_t total_display_time;
        if (thiz->m_ptr_state->equals(&HIDING)) {
            total_display_time = thiz->m_hiding_time;
            current_display_time = total_display_time;
        } else if (thiz->m_ptr_state->equals(&PLAYING)) {
            total_display_time = thiz->m_playing_time;
            current_display_time = total_display_time;
        } else {
            Serial.printf(":: task_countdown :: nothing to countdown in state %s\n", thiz->m_ptr_state->m_name.c_str());
            vTaskDelete(NULL);
        }

        int32_t elapsed_time = 0;
        TickType_t xMaxBlockTime;
        bool should_stop = false;
        while (!should_stop)
        {
            elapsed_time = total_display_time - uint16_t((esp_timer_get_time() - start_time) / 1000000);
            if (elapsed_time > 0) {
                elapsed_time = total_display_time - uint16_t((esp_timer_get_time() - start_time) / 1000000);
                if (current_display_time > elapsed_time) {
                    current_display_time = elapsed_time;
                    thiz->m_display->draw_middle(current_display_time);
                    if (thiz->m_ptr_state->equals(&PLAYING)) {
                        thiz->m_current_playing_time = current_display_time;
                    }
                }

                xMaxBlockTime = pdMS_TO_TICKS( 100 );
            } else {
                // elapsed time has passed
                current_display_time = 0;
                thiz->m_display->draw_middle(current_display_time);
                if (thiz->m_ptr_state->equals(&PLAYING)) {
                    thiz->m_current_playing_time = current_display_time;
                }

                thiz->set_event(&COUNTDOWN_END);
                xMaxBlockTime = portMAX_DELAY; // wait forever to get notified
            }

            // check if notified
            BaseType_t xResult;
            xResult = ulTaskNotifyTake(pdTRUE, xMaxBlockTime);  /* pdTRUE = clear bits on entry. */
            if ( xResult == pdPASS ) {
                Serial.println(":: task_countdown :: we got notified to stop, killing ourselves.");
                should_stop = true;
            }

        } // while(should_stop)

        vTaskDelay(200/portTICK_PERIOD_MS);
        vTaskDelete(NULL);
        
    } // task_countdown

};


class Flag : public FlagAndPlayer {
public:
    Flag(const Team team, DisplayFlag* df) : FlagAndPlayer(team, df) {
        type_name = flag_type_name;
        reinterpret_cast<DisplayFlag*>(m_display)->init();
    }

protected:

    void practicing() override {
        Serial.println("Flag::practicing");
        reinterpret_cast<DisplayFlag*>(m_display)->init();

        TaskHandle_t* ptr_task_receive_ir;
        xTaskCreatePinnedToCore(
            this->task_receive_ir,  //Function to implement the task 
            "task_receive_ir",      //Name of the task
            5000,                   //Stack size in words 
            this,                   //Task input parameter 
            taskPriority,           //Priority of the task 
            ptr_task_receive_ir,    //Task handle.
            taskCore);              //Core where the task should run
        
        add_task(ptr_task_receive_ir);

        vTaskDelay(10 / portTICK_PERIOD_MS);

        blasterLink.set_trigger_action(false, false, false, true); // disable trigger

        FlagAndPlayer::practicing();
    }

    void playing() override {
        Serial.println("Flag::playing");

        TaskHandle_t* ptr_task_receive_ir;
        xTaskCreatePinnedToCore(
            this->task_receive_ir,  //Function to implement the task 
            "task_receive_ir",      //Name of the task
            5000,                   //Stack size in words 
            this,                   //Task input parameter 
            taskPriority,           //Priority of the task 
            ptr_task_receive_ir,    //Task handle.
            taskCore);              //Core where the task should run
        
        add_task(ptr_task_receive_ir);
        
        FlagAndPlayer::playing();
    }

    static void task_receive_ir(void* pvParameter) {
        Flag* thiz = reinterpret_cast<Flag*>(pvParameter); // pointer to our Flag instance
        badgeIrReceiver.start_listen();

        bool should_stop = false;
        while(!should_stop) {
            badgeIrReceiver.receive_ir_data();

            while (badgeIrReceiver.message_available()) {
                DataPacket message = badgeIrReceiver.pop_message();

                Serial.print("-Ir_link: ");
                message.print(&Serial);

                // incoming enemy fire after hit_timeout of previous shot
                if (message.get_command() == eCommandShoot && 
                    message.get_team() != thiz->m_team.team_color() &&
                    thiz->m_last_hit_time + thiz->m_hit_timeout*1000000 < message.get_time_micros()) {

                    thiz->m_health -= thiz->m_hit_damage;
                    thiz->m_last_hit_time = message.get_time_micros();
                }

            }

            // check if notified
            BaseType_t xResult;
            const TickType_t xMaxBlockTime = pdMS_TO_TICKS( 100 );
            xResult = ulTaskNotifyTake(pdTRUE, xMaxBlockTime);  /* pdTRUE = clear bits on entry. */
            if ( xResult == pdPASS ) {
                Serial.println(":: task_receive_ir :: we got notified to stop, killing ourselves.");
                should_stop = true;
            }

        } // while(should_stop)

        badgeIrReceiver.stop_listen();

        vTaskDelay(200/portTICK_PERIOD_MS);
        vTaskDelete(NULL);
        
    } // task_receive_ir

}; //class Flag

class Player : public FlagAndPlayer {
public:
    Player(const Team team, DisplayPlayer* df) : FlagAndPlayer(team, df) {
        type_name = player_type_name;
        reinterpret_cast<DisplayPlayer*>(m_display)->init();
    }

protected:
    uint8_t m_ammo;

    void practicing() {
        Serial.println("Player::practicing");
        reinterpret_cast<DisplayPlayer*>(m_display)->init();
        m_ammo = 100;
        reinterpret_cast<DisplayPlayer*>(m_display)->draw_upper_right(m_ammo);

        TaskHandle_t* ptr_task_receive_ir;
        xTaskCreatePinnedToCore(
            this->task_receive_ir,  //Function to implement the task 
            "task_receive_ir",      //Name of the task
            5000,                   //Stack size in words 
            this,                   //Task input parameter 
            taskPriority,           //Priority of the task 
            ptr_task_receive_ir,    //Task handle.
            taskCore);              //Core where the task should run
        
        add_task(ptr_task_receive_ir);

        TaskHandle_t* ptr_task_blaster_link;
        xTaskCreatePinnedToCore(
            this->task_blaster_link, //Function to implement the task 
            "task_blaster_link",     //Name of the task
            5000,                    //Stack size in words 
            this,                    //Task input parameter 
            taskPriority,            //Priority of the task 
            ptr_task_blaster_link,   //Task handle.
            taskCore);               //Core where the task should run
        
        add_task(ptr_task_blaster_link);

        vTaskDelay(10 / portTICK_PERIOD_MS);

        blasterLink.set_trigger_action(false, false, false, false); // enable trigger

        FlagAndPlayer::practicing();
    }

    void playing() override {
        Serial.println("Player::playing");

        TaskHandle_t* ptr_task_receive_ir;
        xTaskCreatePinnedToCore(
            this->task_receive_ir,  //Function to implement the task 
            "task_receive_ir",      //Name of the task
            5000,                   //Stack size in words 
            this,                   //Task input parameter 
            taskPriority,           //Priority of the task 
            ptr_task_receive_ir,    //Task handle.
            taskCore);              //Core where the task should run
        
        add_task(ptr_task_receive_ir);

        TaskHandle_t* ptr_task_blaster_link;
        xTaskCreatePinnedToCore(
            this->task_blaster_link, //Function to implement the task 
            "task_blaster_link",     //Name of the task
            5000,                    //Stack size in words 
            this,                    //Task input parameter 
            taskPriority,            //Priority of the task 
            ptr_task_blaster_link,   //Task handle.
            taskCore);               //Core where the task should run
        
        add_task(ptr_task_blaster_link);

        vTaskDelay(10 / portTICK_PERIOD_MS);

        blasterLink.set_trigger_action(false, false, false, false); // enable trigger

        FlagAndPlayer::playing();
    }

    static void task_receive_ir(void* pvParameter) {
        Player* thiz = reinterpret_cast<Player*>(pvParameter); // pointer to our Player instance
        badgeIrReceiver.start_listen();

        bool should_stop = false;
        while(!should_stop) {
            badgeIrReceiver.receive_ir_data();

            while (badgeIrReceiver.message_available()) {
                DataPacket message = badgeIrReceiver.pop_message();

                Serial.print("-Ir_link: ");
                message.print(&Serial);

                // incoming enemy fire after hit_timeout of previous shot
                if (message.get_command() == eCommandShoot && 
                    message.get_team() != thiz->m_team.team_color() &&
                    thiz->m_last_hit_time + thiz->m_hit_timeout*1000000 < message.get_time_micros()) {

                    thiz->m_health -= thiz->m_hit_damage;
                    thiz->m_last_hit_time = message.get_time_micros();
                }

            }

            // check if notified
            BaseType_t xResult;
            const TickType_t xMaxBlockTime = pdMS_TO_TICKS( 100 );
            xResult = ulTaskNotifyTake(pdTRUE, xMaxBlockTime);  /* pdTRUE = clear bits on entry. */
            if ( xResult == pdPASS ) {
                Serial.println(":: task_receive_ir :: we got notified to stop, killing ourselves.");
                should_stop = true;
            }

        } // while(should_stop)

        badgeIrReceiver.stop_listen();

        vTaskDelay(200/portTICK_PERIOD_MS);
        vTaskDelete(NULL);
        
    } // task_receive_ir

    static void task_blaster_link(void* pvParameter) {
        Player* thiz = reinterpret_cast<Player*>(pvParameter); // pointer to our Player instance
        blasterLink.start_listen();

        bool should_stop = false;
        while(!should_stop) {
            blasterLink.process_buffer();
            
            while (blasterLink.message_available()) {
                DataPacket message = blasterLink.pop_message();

                Serial.print("-Blaster_link: ");
                message.print(&Serial);

                // incoming enemy fire after hit_timeout of previous shot
                if (message.get_command() == eCommandShoot && 
                    message.get_team() != thiz->m_team.team_color() &&
                    thiz->m_last_hit_time + thiz->m_hit_timeout*1000000 < message.get_time_micros()) {

                    thiz->m_health -= thiz->m_hit_damage;
                    thiz->m_last_hit_time = message.get_time_micros();
                } else
                if (message.get_command() == eCommandShoot && 
                    message.get_team() == thiz->m_team.team_color()) {

                    thiz->m_ammo -= thiz->m_shot_ammo;
                    reinterpret_cast<DisplayPlayer*>(thiz->m_display)->draw_upper_right(thiz->m_ammo);
                    Serial.printf("Shoot ==> new_ammo: %d\n", thiz->m_ammo);

                    // start ammo reloading animation
                    if (thiz->m_ammo <= 0) {
                        // blaster shoot animation is still running
                        // try to disable as soon as possible, before trigger is pressed on blaster again
                        // if waiting too long a new eCommandShoot action might be received
                        vTaskDelay(400/portTICK_PERIOD_MS);
                        blasterLink.set_trigger_action(false, false, false, true); // disable shooting

                        uint8_t total_reload_time_seconds = 5;
                        uint8_t total_reload_time_steps = 100;
                        int64_t reload_time_interval_us = total_reload_time_seconds * 1000000 / total_reload_time_steps;

                        uint16_t buzzer_start_freq = 400;
                        uint16_t buzzer_end_freq = 1400;
                        Badge2020_Buzzer buzzer;
                        buzzer.setVolume(255);
                        
                        Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
                        const float led_step = 255.0f / total_reload_time_steps * total_reload_time_seconds;
                        strip.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
                        strip.clear();
                        strip.show();            // Turn OFF all pixels ASAP
                        strip.setBrightness(50); // Set BRIGHTNESS to about 1/5 (max = 255)

                        bool reloading = true;

                        int64_t start_time = esp_timer_get_time();
                        int64_t last_reload_time = start_time;
                        while(reloading) {
                            int64_t current_time = esp_timer_get_time();
                            if (current_time - last_reload_time > reload_time_interval_us) {
                                uint8_t new_ammo = uint8_t( (current_time - start_time) / reload_time_interval_us );
                                if (new_ammo >= 100) {
                                    new_ammo = 100;
                                    reloading = false;
                                }
                                thiz->m_ammo = new_ammo;
                                reinterpret_cast<DisplayPlayer*>(thiz->m_display)->draw_upper_right(thiz->m_ammo);

                                // value between nem_ammo=0 -> start_freq and new_ammo=100 -> end_freq
                                buzzer.setFrequency(buzzer_start_freq + (new_ammo * (buzzer_end_freq - buzzer_start_freq) / total_reload_time_steps) );

                                // set the value of each led, so that new_ammo=0 is all leds at 0 and new_ammo=100 is all leds at 255
                                for(uint8_t led = 0; led < LED_COUNT; led++) {
                                    uint8_t c = 0;
                                    if (new_ammo < (led) * total_reload_time_steps / LED_COUNT) {
                                        c = 0;
                                    } else if (new_ammo > (led+1) * total_reload_time_steps / LED_COUNT ) {
                                        c = 255;
                                    } else {
                                        c = (new_ammo - (led * total_reload_time_steps / LED_COUNT)) * led_step;
                                    }
                                    strip.setPixelColor(led, c, c, c);
                                }
                                strip.show();

                                last_reload_time = esp_timer_get_time();;
                            }
                            vTaskDelay(reload_time_interval_us / 1000 / 2 / portTICK_PERIOD_MS);
                        }
                        buzzer.setVolume(0);

                        strip.clear();
                        strip.show();            // Turn OFF all pixels ASAP

                        blasterLink.set_trigger_action(false, false, false, false); // enable shooting
                    } 
                    // end ammo reloading animation

                }

            }

            // check if notified
            BaseType_t xResult;
            const TickType_t xMaxBlockTime = pdMS_TO_TICKS( 100 );
            xResult = ulTaskNotifyTake(pdTRUE, xMaxBlockTime);  /* pdTRUE = clear bits on entry. */
            if ( xResult == pdPASS ) {
                Serial.println(":: task_blaster_link :: we got notified to stop, killing ourselves.");
                should_stop = true;
            }

        } // while(should_stop)

        blasterLink.stop_listen();

        vTaskDelay(200/portTICK_PERIOD_MS);
        vTaskDelete(NULL);
        
    } // task_blaster_link

}; // class Player


Flag FLAG_REX_PROFILE = Flag(REX, &DISPLAY_FLAG_REX);
Flag FLAG_GIGGLE_PROFILE = Flag(GIGGLE, &DISPLAY_FLAG_GIGGLE);
Flag FLAG_BUZZ_PROFILE = Flag(BUZZ, &DISPLAY_FLAG_BUZZ);
Player PLAYER_REX_PROFILE = Player(REX, &DISPLAY_PLAYER_REX);
Player PLAYER_GIGGLE_PROFILE = Player(GIGGLE, &DISPLAY_PLAYER_GIGGLE);
Player PLAYER_BUZZ_PROFILE = Player(BUZZ, &DISPLAY_PLAYER_BUZZ);

#endif
