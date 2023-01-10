
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

    Event* run(State *ptr_state) override {
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
        std::vector<Profile*> profiles = Profile::find_profiles();
        uint8_t rnd_index = random(profiles.size());
        CONFIRM_PROFILE.set_new_model(reinterpret_cast<Model*>(profiles[rnd_index]));
        set_event(&CONFIRM_PROFILE);
    }

    virtual void _practicing() {
        Serial.println("FlagAndPlayer::_practicing");
        blasterLink.set_team(m_team.team_color());
        m_display->draw_static_middle(m_ptr_state->m_name);
        m_health = 100;
        m_display->draw_upper_left(m_health);
        set_event(&PRESTART);
    }

    void _hiding() {
        set_event(&COUNTDOWN_END);
    }

    void _playing() {
        set_event(&COUNTDOWN_END);
    }

    void _finishing() {
        set_event(&BOOT);
        //set_event(&NEXT_ROUND);
    }

protected:
    Display* m_display;
    State* m_ptr_state;
    uint8_t m_health;
    const Team m_team;
};


class Flag : public FlagAndPlayer {
public:
    Flag(const Team team, DisplayFlag* df) : FlagAndPlayer(team, df) {
        reinterpret_cast<DisplayFlag*>(m_display)->init();
    }

    void _practicing() override {
        Serial.println("Flag::_practicing");
        reinterpret_cast<DisplayFlag*>(m_display)->init();
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
        FlagAndPlayer::_practicing();
        m_ammo = 100;
        reinterpret_cast<DisplayPlayer*>(m_display)->draw_upper_right(m_ammo);
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
