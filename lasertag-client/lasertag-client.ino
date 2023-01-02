#include <Badge2020_TFT.h>

#define PLAYING_TIME 300

Badge2020_TFT tft;

uint16_t ConvertRGB(const uint8_t &R, const uint8_t &G, const uint8_t &B)
{
  return ( ((R & 0xF8) << 8) | ((G & 0xFC) << 3) | (B >> 3) );
}

class Team
{
public:
  Team(const uint8_t &color, const std::string &name) : m_color(color), m_name(name)
  {}
  
  uint16_t color() const {
    return m_color;
  }

  std::string name() const {
    return m_name;
  }

private:
  const uint8_t m_color;
  const std::string m_name;
};

const Team team_rex(ConvertRGB(255, 0, 0), "Rex");
const Team team_giggle(ConvertRGB(0, 140, 0), "Giggle");
const Team team_buzz(ConvertRGB(0, 0, 210), "Buzz");

class Display
{
public:
  Display(const Team &team): m_color(team.color()), m_team_name(team.name())
  {}
  
  void init()
  {
    draw_borders();
    draw_static_upper_left();
  }

  void draw_upper_left(const uint8_t health)
  {
    tft.setCursor(m_width + 18, 37);
    tft.setTextColor(m_color);
    tft.setTextSize(3);
    tft.print(health);
  }

  void draw_static_middle(const std::string txt)
  {
    // middle bg_color
    tft.fillRect(m_width, 82 + int(m_width / 2), 240 - m_width * 2, 109, m_bg_color);
    tft.setCursor(8+38, 92);
    tft.setTextColor(m_color);
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
  const uint8_t m_width = 8;
  const uint16_t m_bg_color = ST77XX_WHITE;
  const uint16_t m_color;
  const std::string m_team_name;

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
    tft.setTextColor(m_color);
    tft.setTextSize(2);
    tft.print("Health%");
  }

  virtual void draw_static_upper_right() = 0;

  void draw_static_bottom()
  {
    // bottom bg_color
    tft.fillRect(m_width, 199 + int(m_width / 2), 240 - m_width * 2, 29, m_bg_color);
  }
};


class DisplayPlayer: public Display
{
public:
  DisplayPlayer(const Team &team) : Display(team)
  {
  }

  void init()
  {
    Display::init();
    draw_static_upper_right();
    draw_static_bottom();
  }

  void draw_upper_right(const uint8_t ammo)
  {
    tft.setCursor(120 + int(m_width / 2) + 18, 37);
    tft.setTextColor(m_color);
    tft.setTextSize(3);
    tft.print(ammo);
  }
protected:
  void draw_static_upper_right() {
    // upper right bg_color
    tft.fillRect(120 + int(m_width / 2), m_width, 120 - m_width - int(m_width / 2), 82 - int(1.5 * m_width), m_bg_color);
    tft.setCursor(120 + 4 + 6, 14);
    tft.setTextColor(m_color);
    tft.setTextSize(2);
    tft.print("Ammo%");
  }

  void draw_static_bottom()
  {
    Display::draw_static_bottom();
    tft.setCursor(8 + 50, 209);
    tft.setTextColor(m_color);
    tft.setTextSize(2);
    std::string txt = "Player " + m_team_name;
    tft.print(txt.c_str());
  }
};


DisplayPlayer display(team_buzz);

long long startMicros = esp_timer_get_time();
long long lastMicrosCountdown = 0;
const long countdownInterval = 1000000; // 1 second
uint16_t playing_time = PLAYING_TIME;

void setup(void) {
  Serial.begin(115200);

  tft.init(240, 240);
  tft.setRotation( 2 );

  // Anything from the Adafruit GFX library can go here, see
  // https://learn.adafruit.com/adafruit-gfx-graphics-library
  
  tft.fillScreen(ST77XX_BLACK);
  
  display.init();
  display.draw_upper_left(100);
  display.draw_upper_right(100);
  display.draw_static_middle("countdown");

}

void loop() {
  startMicros = esp_timer_get_time();

  if (startMicros - lastMicrosCountdown >= countdownInterval)
  {
    lastMicrosCountdown = startMicros;
    
    Serial.println(playing_time);

    display.draw_middle(playing_time);
    
    playing_time--;
    if (playing_time > PLAYING_TIME) 
    {
      playing_time = PLAYING_TIME;
    }
  }





}