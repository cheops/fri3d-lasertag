#ifndef MVP_HPP
#define MVP_HPP

#include "team.hpp"
#include "display.hpp"
#include "statemachine.hpp"

static const uint16_t HIDING_TIME = 10;
static const uint16_t PLAYING_TIME = 60 * 2;
static const uint8_t HIT_DAMAGE = 30;
static const uint8_t HIT_TIMEOUT = 5;
static const uint8_t SHOT_AMMO = 1;

static const uint8_t PRACTICINT_CHANNEL = 2;
static const uint8_t PLAYING_CHANNEL = 3;
static const uint8_t INVALID_CHANNEL = 15;


const Team REX(ConvertRGB(255, 0, 0), "Rex");
const Team GIGGLE(ConvertRGB(0, 140, 0), "Giggle");
const Team BUZZ(ConvertRGB(0, 0, 210), "Buzz");


State BOOTING = State("booting");
State PRACTICING = State("practicing");
State HIDING = State("hiding");
State PLAYING = State("playing");
State FINISHING = State("finishing");

Event BOOT = Event("boot");
Event CONFIRM_PROFILE = Event("confirm_profile");
Event PRESTART = Event("prestart");
Event COUNTDOWN_END = Event("countdown_end");
Event DEAD = Event("dead");
Event NEXT_ROUND = Event("next_round");

static const uint8_t TRANSITIONS_COUNT = 7;
Transition TRANSITIONS_MVP[TRANSITIONS_COUNT] = {
    Transition(&CONFIRM_PROFILE, &BOOTING, &PRACTICING),
    Transition(&PRESTART, &PRACTICING, &HIDING),
    Transition(&COUNTDOWN_END, &HIDING, &PLAYING),
    Transition(&COUNTDOWN_END, &PLAYING, &FINISHING),
    Transition(&DEAD, &PLAYING, &FINISHING),
    Transition(&BOOT, &FINISHING, &BOOTING),
    Transition(&NEXT_ROUND, &FINISHING, &PRACTICING),
};

DisplayFlag DISPLAY_FLAG_REX = DisplayFlag(REX);
DisplayFlag DISPLAY_FLAG_GIGGLE = DisplayFlag(GIGGLE);
DisplayFlag DISPLAY_FLAG_BUZZ = DisplayFlag(BUZZ);
DisplayPlayer DISPLAY_PLAYER_REX = DisplayPlayer(REX);
DisplayPlayer DISPLAY_PLAYER_GIGGLE = DisplayPlayer(GIGGLE);
DisplayPlayer DISPLAY_PLAYER_BUZZ = DisplayPlayer(BUZZ);



#endif