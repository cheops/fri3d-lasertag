#ifndef TEAM_HPP
#define TEAM_HPP

#include <stdint.h>
#include <string>
#include "blaster_packet.hpp"

class Team
{
public:
  Team(const uint16_t &screen_color, const uint32_t &led_color, const std::string &name, const TeamColor team_color) 
  : m_screen_color(screen_color), m_led_color(led_color), m_name(name), m_team_color(team_color)
  {}
  
  uint16_t screen_color() const {
    return m_screen_color;
  }

  uint32_t led_color() const {
    return m_led_color;
  }

  std::string name() const {
    return m_name;
  }

  TeamColor team_color() const {
    return m_team_color;
  }

private:
  const uint16_t m_screen_color;
  const uint32_t m_led_color;
  const std::string m_name;
  const TeamColor m_team_color;
};

#endif