
#ifndef PROFILE_MVP_HPP
#define PROFILE_MVP_HPP

#include "profile.hpp"
#include "statemachine.hpp"
#include "team.hpp"
#include "mvp.hpp"

class FlagAndPlayer: public Profile, public Model {
public:
    FlagAndPlayer(const Team team) : Profile(), Model(), m_team(team) {
        Serial.printf("Create Profile FlagAndPlayer %s\n", team.name().c_str());
        m_display.init();
    }
    const Event* run(State state) {
        Serial.printf("FlagAndPlayer::run state:%s\n", state);
        m_state = state;
        if (state == BOOTING) _booting();
        else if (state == PRACTICING) _practicing();
        else if (state == HIDING) _hiding();
        else if (state == PLAYING) _playing();
        else if (state == FINISHING) _finishing();
        
        return Model::run(state);
    }
protected:
    const Team m_team;
    Display m_display;
    State m_state;
    uint8_t m_health;

    void _booting() {
        m_display.draw_static_middle(m_state.m_name);

        delay(1000);
        Model::set_event(&CONFIRM_PROFILE);
    }

    const Event* listen_ble_preStart() {
        bleClient.start_listen(eBleMessageTypePrestart);
        while (!bleClient.listen_type_found())
        {
            vTaskDelay(1000/portTICK_PERIOD_MS);
        }
        
        bleClient.get_ble_message().print(&Serial);
        bleClient.reset();
        return &PRESTART;
    }

    void _practicing() {
        m_health = 100;
        m_display.init();
        m_display.draw_static_middle(m_state.m_name);
        m_display.draw_middle(0);
        m_display.draw_upper_left(m_health);

        const Event* new_event = listen_ble_preStart();
        Model::set_event(new_event);
    }
    void _hiding() {
        m_health = 100;
        m_display.init();
        m_display.draw_static_middle(m_state.m_name);
        m_display.draw_middle(0);
        m_display.draw_upper_left(m_health);
    }

    void _playing() {
        m_health = 100;
        m_display.init();
        m_display.draw_static_middle(m_state.m_name);
        m_display.draw_middle(0);
        m_display.draw_upper_left(m_health);
        m_display.draw_static_middle(m_state.m_name);
    }
    
    const Event* liste_ble_nextRound() {
        bleClient.start_listen(eBleMessageTypeNextRound);
        while (!bleClient.listen_type_found())
        {
            vTaskDelay(1000/portTICK_PERIOD_MS);
        }
        
        bleClient.get_ble_message().print(&Serial);
        bleClient.reset();

        return &NEXT_ROUND;

    }

    void _finishing() {
        m_health = 100;
        m_display.init();
        m_display.draw_static_middle(m_state.m_name);
        m_display.draw_middle(0);
        m_display.draw_upper_left(m_health);
        m_display.draw_static_middle(m_state.m_name);

        const Event* new_event = listen_ble_preStart();
        Model::set_event(new_event);
    }

};

class Flag : public FlagAndPlayer {
public:
    Flag(const Team team) : FlagAndPlayer(team) {
        Serial.printf("Create Profile Flag %s\n", team.name().c_str());
        m_display = DisplayFlag(team);
    }

    const Event* run(State state) {
        Serial.printf("Flag::run state:%s\n", state);
        return FlagAndPlayer::run(state);
    }

private:


};

class Player: public FlagAndPlayer {
public:
    Player(const Team team) : FlagAndPlayer(team) {
        Serial.printf("Create Profile Player %s\n", team.name().c_str());
        m_display = DisplayPlayer(team);
    }

    const Event* run(State state) {
        Serial.printf("Player::run state:%s\n", state);
        return FlagAndPlayer::run(state);
    }

    void _booting() {
        FlagAndPlayer::_booting();
    }


private:

};


#endif
