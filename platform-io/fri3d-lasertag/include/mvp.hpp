#ifndef MVP_HPP
#define MVP_HPP

#include "team.hpp"
#include "display.hpp"

static const int PLAYING_TIME = 300;


const Team team_rex(ConvertRGB(255, 0, 0), "Rex");
const Team team_giggle(ConvertRGB(0, 140, 0), "Giggle");
const Team team_buzz(ConvertRGB(0, 0, 210), "Buzz");

DisplayPlayer display(team_rex);


#endif