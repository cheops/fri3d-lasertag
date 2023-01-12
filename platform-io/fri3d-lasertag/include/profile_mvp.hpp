
#ifndef PROFILE_MVP_HPP
#define PROFILE_MVP_HPP

#include "profile.hpp"
#include "statemachine.hpp"
#include "team.hpp"
#include "mvp.hpp"
#include "blaster_link.hpp"

class FlagAndPlayer : public Profile, public Model {
public:
    FlagAndPlayer(const Team team, Display* df) : Profile(), Model(), m_display(df), m_team(team) {
        Serial.printf("Create FlagAndPlayer Model %s\n", team.name().c_str());
    }

    Event* run(State* ptr_state) override {
        Serial.printf("FlagAndPlayer::run state:%s\n", ptr_state->m_name.c_str());
        m_ptr_state = ptr_state;

        m_display->draw_static_middle(m_ptr_state->m_name);

        if (m_ptr_state->equals(&BOOTING)) _booting();
        else if (m_ptr_state->equals(&PRACTICING)) _practicing();
        else if (m_ptr_state->equals(&HIDING)) _hiding();
        else if (m_ptr_state->equals(&PLAYING)) _playing();
        else if (m_ptr_state->equals(&FINISHING)) _finishing();

        delay(2000);
        return Model::run(m_ptr_state);
    }

    void _booting() {
        Serial.println("FlagAndPlayer::_booting");
        
        // fetch all registered profiles and select a random one as the new StateMachineModel
        std::vector<Profile*> profiles = Profile::find_profiles();
        uint8_t rnd_index = random(profiles.size());
        Profile* ptr_new_profile = profiles[rnd_index];
        
        // not really needed, start of practicing will start with the new Model, and the FlagAndPlayer::m_team will be set correctly
        FlagAndPlayer* ptr_fap = reinterpret_cast<FlagAndPlayer*>(ptr_new_profile);;
        const Team new_team = ptr_fap->m_team;
        blasterLink.set_team(new_team.team_color());
        
        // set the new Model on the Event, so that a Model swich happens in the StateMachine
        Model* ptr_new_model = reinterpret_cast<Model*>(ptr_new_profile);
        CONFIRM_PROFILE.set_new_model(ptr_new_model);
        set_event(&CONFIRM_PROFILE);
    }

    virtual void _practicing() {
        Serial.println("FlagAndPlayer::_practicing");
        blasterLink.set_team(m_team.team_color());
        blasterLink.set_channel(m_practicing_channel);

        m_display->draw_static_middle(m_ptr_state->m_name);
        m_health = 100;
        m_display->draw_upper_left(m_health);

        bleClient.start_listen(eBleMessageTypePrestart);
        
        // wait for ble_message
        while (!bleClient.listen_type_found())
        {
            // practicing loop
            vTaskDelay(500/portTICK_PERIOD_MS);
        }
        
        BleMessage ble_message = bleClient.get_ble_message();
        m_hiding_time = ble_message.get_hiding_time();
        m_playing_time = ble_message.get_playing_time();
        m_hit_damage = ble_message.get_hit_damage();
        m_hit_timeout = ble_message.get_hit_timeout();
        m_shot_ammo = ble_message.get_shot_ammo();
        m_practicing_channel = ble_message.get_practicing_channel();
        m_playing_channel = ble_message.get_playing_channel();
        m_mqtt_game_id = ble_message.get_mqtt_game_id();
        m_mqtt_during_playing = ble_message.get_mqtt_during_playing();
        
        set_event(&PRESTART);
    }

    void _hiding() {
        uint64_t start_hiding_time = esp_timer_get_time();
        uint8_t current_hiding_time = m_hiding_time;
        Serial.println("FlagAndPlayer::_hiding");

        blasterLink.set_trigger_action(false, false, false, true); // disable trigger

        // hiding loop
        bool keep_hiding = true;
        while(keep_hiding) {
            uint64_t current_time = esp_timer_get_time();
            if (current_time - start_hiding_time >= m_hiding_time * 1000000) {
                // time is up
                set_event(&COUNTDOWN_END);
                keep_hiding = false;
            }

            // more time has elapsed then we have drawn on the display
            uint16_t elapsed_hiding_time = m_hiding_time - uint16_t((current_time - start_hiding_time) / 1000000);
            if ( current_hiding_time > elapsed_hiding_time ) {
                current_hiding_time = elapsed_hiding_time;
                m_display->draw_middle(current_hiding_time);
            }

            vTaskDelay(100/portTICK_PERIOD_MS);
        }
    }

    virtual void _playing() {
        uint64_t start_playing_time = esp_timer_get_time();
        m_current_playing_time = m_playing_time;
        Serial.println("FlagAndPlayer::_playing");
        blasterLink.set_channel(m_playing_channel);

        // playing loop
        bool keep_playing = true;
        while(keep_playing) {
            uint64_t current_time = esp_timer_get_time();
            if (current_time - start_playing_time >= m_playing_time * 1000000) {
                // time is up
                set_event(&COUNTDOWN_END);
                keep_playing = false;
            }

            // more time has elapsed then we have drawn on the display
            uint16_t elapsed_playing_time = m_playing_time - uint16_t((current_time - start_playing_time) / 1000000);
            if ( m_current_playing_time > elapsed_playing_time ) {
                m_current_playing_time = elapsed_playing_time;
                m_display->draw_middle(m_current_playing_time);
            }

            vTaskDelay(100/portTICK_PERIOD_MS);
        }
    }

    void _finishing() {
        Serial.println("FlagAndPlayer::_finishing");
        blasterLink.set_channel(INVALID_CHANNEL);
        blasterLink.set_trigger_action(false, false, false, true); // disable trigger

        m_display->draw_middle(m_current_playing_time);


        bleClient.start_listen(eBleMessageTypeNextRound);
        
        // wait for ble_message
        while (!bleClient.listen_type_found())
        {
            vTaskDelay(500/portTICK_PERIOD_MS);
        }
        
        BleMessage ble_message = bleClient.get_ble_message();
        m_hiding_time = ble_message.get_hiding_time();
        m_playing_time = ble_message.get_playing_time();
        m_hit_damage = ble_message.get_hit_damage();
        m_hit_timeout = ble_message.get_hit_timeout();
        m_shot_ammo = ble_message.get_shot_ammo();
        m_practicing_channel = ble_message.get_practicing_channel();
        m_playing_channel = ble_message.get_playing_channel();
        m_mqtt_game_id = ble_message.get_mqtt_game_id();
        m_mqtt_during_playing = ble_message.get_mqtt_during_playing();
        
        //set_event(&BOOT);
        set_event(&NEXT_ROUND);
    }

protected:
    Display* m_display;
    State* m_ptr_state;
    uint8_t m_health;
    const Team m_team;
    uint16_t m_hiding_time = HIDING_TIME;
    uint16_t m_playing_time = PLAYING_TIME;
    uint16_t m_current_playing_time = PLAYING_TIME;
    uint8_t m_hit_damage = HIT_DAMAGE;
    uint8_t m_hit_timeout = HIT_TIMEOUT;
    uint8_t m_shot_ammo = SHOT_AMMO;
    uint8_t m_practicing_channel = PRACTICING_CHANNEL;
    uint8_t m_playing_channel = PLAYING_CHANNEL;
    uint32_t m_mqtt_game_id;
    bool m_mqtt_during_playing;

};


class Flag : public FlagAndPlayer {
public:
    Flag(const Team team, DisplayFlag* df) : FlagAndPlayer(team, df) {
        reinterpret_cast<DisplayFlag*>(m_display)->init();
    }

    void _practicing() override {
        Serial.println("Flag::_practicing");
        reinterpret_cast<DisplayFlag*>(m_display)->init();

        blasterLink.set_trigger_action(false, false, false, true); // disable trigger

        FlagAndPlayer::_practicing();
    }

};

class Player : FlagAndPlayer {
public:
    Player(const Team team, DisplayPlayer* df) : FlagAndPlayer(team, df) {
        reinterpret_cast<DisplayPlayer*>(m_display)->init();
    }

    void _practicing() {
        Serial.println("Player::_practicing");
        reinterpret_cast<DisplayPlayer*>(m_display)->init();
        m_ammo = 100;
        reinterpret_cast<DisplayPlayer*>(m_display)->draw_upper_right(m_ammo);

        blasterLink.set_trigger_action(false, false, false, false); // enable trigger

        FlagAndPlayer::_practicing();
    }

    void _playing() override {
        blasterLink.set_trigger_action(false, false, false, false); // enable trigger

        FlagAndPlayer::_playing();
    }
protected:
    uint8_t m_ammo;
};


Player PLAYER_REX_PROFILE = Player(REX, &DISPLAY_PLAYER_REX);
Player PLAYER_GIGGLE_PROFILE = Player(GIGGLE, &DISPLAY_PLAYER_GIGGLE);
Player PLAYER_BUZZ_PROFILE = Player(BUZZ, &DISPLAY_PLAYER_BUZZ);
Flag FLAG_REX_PROFILE = Flag(REX, &DISPLAY_FLAG_REX);
Flag FLAG_GIGGLE_PROFILE = Flag(GIGGLE, &DISPLAY_FLAG_GIGGLE);
Flag FLAG_BUZZ_PROFILE = Flag(BUZZ, &DISPLAY_FLAG_BUZZ);

#endif
