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


const State BOOTING = State("booting");
const State PRACTICING = State("practicing");
const State HIDING = State("hiding");
const State PLAYING = State("playing");
const State FINISHING = State("finishing");

const Event BOOT = Event("boot");
const Event CONFIRM_PROFILE = Event("confirm_profile");
const Event PRESTART = Event("prestart");
const Event COUNTDOWN_END = Event("countdown_end");
const Event DEAD = Event("dead");
const Event NEXT_ROUND = Event("next_round");

Transition transitions_mvp[] = {
    Transition(CONFIRM_PROFILE, BOOTING, PRACTICING),
    Transition(PRESTART, PRACTICING, HIDING),
    Transition(COUNTDOWN_END, HIDING, PLAYING),
    Transition(COUNTDOWN_END, PLAYING, FINISHING),
    Transition(DEAD, PLAYING, FINISHING),
    Transition(BOOT, FINISHING, BOOTING),
    Transition(NEXT_ROUND, FINISHING, PRACTICING),
};

#endif