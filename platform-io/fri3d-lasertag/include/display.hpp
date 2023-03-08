#ifndef DISPLAY_HPP
#define DISPLAY_HPP

#include <stdint.h>
#include <Badge2020_TFT.h>

#include "team.hpp"


Badge2020_TFT tft;



/**
 * @brief Convert RGB888 values to RGB565
 * 
 * @param R input 8 bits of Red
 * @param G input 8 bits of Green
 * @param B input 8 bits of Blue
 * @return uint16_t Red 5 bits - G 6 bits - Blue 5 bits
 */
uint16_t ConvertRGB(const uint8_t &R, const uint8_t &G, const uint8_t &B)
{
  return ( ((R & 0xF8) << 8) | ((G & 0xFC) << 3) | (B >> 3) );
}


/*

screen layout = 240 x 240 pixels
border width = 8 pixels
spacer between text and border = 6 pixels

+---------+--------+
| Health  | Ammo   |
|  100%   | 100%   |
+---------+--------+
|    countdown     |
|       0:00       |
+------------------+
|    player buzz   |
+------------------+

*/
class Display
{
public:
  Display() {}
  Display(const Team &team) {
    m_color = team.screen_color();
    m_team_name = team.name();
  }
  
  virtual void init()
  {
    tft.init(240, 240);
    tft.setRotation( 2 );
    tft.fillScreen(ST77XX_BLACK);

    draw_borders();
    draw_static_upper_left();
  }

  void draw_upper_left(const uint8_t health)
  {
    tft.setCursor(m_width + 18, 37);
    tft.setTextColor(m_color, m_bg_color);
    tft.setTextSize(3);
    tft.printf("%3d", health);
  }

  void draw_static_middle(const std::string txt)
  {
    // middle bg_color
    tft.fillRect(m_width, 82 + int(m_width / 2), 240 - m_width * 2, 109, m_bg_color);
    tft.setCursor(8+38, 92);
    tft.setTextColor(m_color, m_bg_color);
    tft.setTextSize(3);
    tft.print(txt.c_str());
  }

  void draw_middle(const uint16_t countdown_seconds)
  {
    uint8_t minutes = countdown_seconds / 60;
    uint8_t seconds = countdown_seconds % 60;
    tft.setCursor(m_width + 44, 121);
    tft.setTextColor(m_color, m_bg_color);
    tft.setTextSize(5);
    tft.printf("%2d:%02d", minutes, seconds);
  }

protected:
  static const uint8_t m_width = 8;
  static const uint16_t m_bg_color = ST77XX_WHITE;
  uint16_t m_color;
  std::string m_team_name;

  void draw_borders()
  {
    for(int i = 0; i < m_width; i ++)
    {
      //border
      tft.drawRect(i, i, 240 - 2 * i, 240 - 2 * i, m_color);
      
      // horizontal divider between upper and middle
      tft.drawFastHLine(m_width, 82 - int(m_width / 2) + i, 240 - 2 * m_width, m_color);

      // vertical divider between upper left and upper right
      tft.drawFastVLine(120 - int(m_width / 2) + i, m_width, 82 - int(1.5 * m_width), m_color);

      // horizontal divider between middle and bottom
      tft.drawFastHLine(m_width, 199 - int(m_width / 2) + i, 240 - 2 * m_width, m_color);
    }
  }

  void draw_static_upper_left()
  {
    // upper left bg_color
    tft.fillRect(m_width, m_width, 120 - m_width - int(m_width / 2), 82 - int(1.5 * m_width), m_bg_color);
    tft.setCursor(8+4, 14);
    tft.setTextColor(m_color, m_bg_color);
    tft.setTextSize(2);
    tft.print("Health%");
  }

  virtual void draw_static_upper_right() {};
  virtual void draw_static_bottom() {
    // bottom bg_color
    tft.fillRect(m_width, 199 + int(m_width / 2), 240 - m_width * 2, 29, m_bg_color);
  };

};


/*

+---------+--------+
| Health% | Ammo%  |
|  100    | 100    |
+---------+--------+
|    countdown     |
|       0:00       |
+------------------+
|    player buzz   |
+------------------+

*/
class DisplayPlayer: public Display
{
public:
  //DisplayPlayer() : Display() {}
  DisplayPlayer(const Team &team) : Display(team) {}

  void init() override
  {
    Display::init();
    draw_static_upper_right();
    draw_static_bottom();
  }

  void draw_upper_right(const uint8_t ammo)
  {
    tft.setCursor(120 + int(m_width / 2) + 18, 37);
    tft.setTextColor(m_color, m_bg_color);
    tft.setTextSize(3);
    tft.printf("%3d", ammo);
  }
protected:
  void draw_static_upper_right() override {
    // upper right bg_color
    tft.fillRect(120 + int(m_width / 2), m_width, 120 - m_width - int(m_width / 2), 82 - int(1.5 * m_width), m_bg_color);
    tft.setCursor(120 + 4 + 6, 14);
    tft.setTextColor(m_color, m_bg_color);
    tft.setTextSize(2);
    tft.print("Ammo%");
  }

  void draw_static_bottom() override
  {
    Display::draw_static_bottom();
    tft.setCursor(8 + 50, 209);
    tft.setTextColor(m_color, m_bg_color);
    tft.setTextSize(2);
    std::string txt = "Player " + m_team_name;
    tft.print(txt.c_str());
  }
};


/*

+---------+--------+
| Health% | Ammo%  |
|  100    | 100    |
+---------+--------+
|    countdown     |
|       0:00       |
+------------------+
|    flag buzz     |
+------------------+

*/
class DisplayFlag: public Display
{
public:
  //DisplayFlag() : Display() {}
  DisplayFlag(const Team &team) : Display(team) {}

  void init() override 
  {
    Display::init();
    draw_static_upper_right();
    draw_static_bottom();
  }

protected:
  void draw_static_upper_right() override {
    // upper right color
    tft.fillRect(120 + int(m_width / 2), m_width, 120 - m_width - int(m_width / 2), 82 - int(1.5 * m_width), m_color);
  }

  void draw_static_bottom() override
  {
    Display::draw_static_bottom();
    tft.setCursor(8 + 50, 209);
    tft.setTextColor(m_color, m_bg_color);
    tft.setTextSize(2);
    std::string txt = "Flag " + m_team_name;
    tft.print(txt.c_str());
  }
};

#endif