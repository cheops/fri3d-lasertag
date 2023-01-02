#include "display.hpp"

#define PLAYING_TIME 300


const Team team_rex(ConvertRGB(255, 0, 0), "Rex");
const Team team_giggle(ConvertRGB(0, 140, 0), "Giggle");
const Team team_buzz(ConvertRGB(0, 0, 210), "Buzz");

DisplayPlayer display(team_rex);

long long startMicros = esp_timer_get_time();
long long lastMicrosCountdown = 0;
const long countdownInterval = 1000000; // 1 second
uint16_t playing_time = PLAYING_TIME;

void setup(void) {
  Serial.begin(115200);
  
  tft.init(240, 240);
  tft.setRotation( 2 );
  tft.fillScreen(ST77XX_BLACK);
  
  display.init();
  display.draw_upper_left(100);
  display.draw_upper_right(100);
  display.draw_static_middle("Playing");

}

void loop() {
  startMicros = esp_timer_get_time();

  if (startMicros - lastMicrosCountdown >= countdownInterval)
  {
    lastMicrosCountdown = startMicros;
    
    //Serial.println(playing_time);

    display.draw_middle(playing_time);
    
    playing_time--;
    if (playing_time > PLAYING_TIME) // uint16_t rollover
    {
      playing_time = PLAYING_TIME;
    }
  }





}