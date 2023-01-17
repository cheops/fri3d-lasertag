//
// board esp32 dev module
// flash size 4096k
// no PSRAM
//
// https://www.espressif.com/sites/default/files/documentation/esp32_bluetooth_architecture_en.pdf
// bluetooth assigned numbers https://www.bluetooth.com/specifications/assigned-numbers/
#include "esp_bt_device.h"

#include <string>

#include <BLEDevice.h>
#include <Fri3dButtons.h>

#define PRESTART_TYPE 1
#define NEXT_ROUND_TYPE 2

#define HIDING_TIME 60*2
#define PLAYING_TIME 60*5
#define HIT_DAMAGE 5
#define HIT_TIMEOUT 3
#define SHOT_AMMO 1
#define PRACTICING_CHANNEL 2
#define PLAYING_CHANNEL 3
#define MQTT_GAME_ID 1234
#define MQTT_DURING_PLAYING 0

#define NEXT_ROUND_REPEAT 120

Fri3dButtons buttons = Fri3dButtons();

bool button0_pressed = false;
bool button1_pressed = false;

int64_t startMicros = esp_timer_get_time();

/**
bluetooth advertisement packet length = 37 bytes
- 6 bytes advertisement address = bluetooth mac address
- 1 byte length
- 1 byte type (0xFF Manufacturer Specific Data)
- x bytes manufacturer specific data (max 29)
  - 2 bytes manufacturer UUID (set to 0xFF 0xFF)
  - y bytes custom data (max 27)

we need to encode the x bytes manufacturer specific data (max 29)
uint8_t message_type (1 byte 0-255)
uint16_t hiding_time (2 bytes 0-65535) seconds
uint16_t playing_time (2 bytes 0-65535) seconds
uint8_t hit_damage (1 byte 0-100) health %
uint8_t hit_timeout (1 byte 0-255) seconds
uint8_t shot_ammo (1 byte 0-100) ammo %
uint8_t practicing_channel (half byte 0-15) 0 is default channel, 3 is default practicing_channel
uint8_t playing_channel (half byte 0-15) 0 is default channel, 4 is default playing_channel
uint32_t mqtt_game_id (4 bytes 0-4294967296)
bool mqtt_during_playing (1 bit 0-1)
*/
std::string encodeManufacturerData(
  uint8_t message_type,
  uint16_t hiding_time,
  uint16_t playing_time,
  uint8_t hit_damage,
  uint8_t hit_timeout,
  uint8_t shot_ammo,
  uint8_t practicing_channel,
  uint8_t playing_channel,
  uint32_t mqtt_game_id,
  bool mqtt_during_playing
  )
  {
    unsigned char manu_data[16];

    manu_data[0] = 0xFF;
    manu_data[1] = 0xFF;

    manu_data[2] = message_type;

    manu_data[3] = (hiding_time >> 8) & 0xFF;
    manu_data[4] = hiding_time & 0xFF;

    manu_data[5] = (playing_time >> 8) & 0xFF;
    manu_data[6] = playing_time & 0xFF;

    manu_data[7] = _min(hit_damage, 100); // limit to 0-100

    manu_data[8] = hit_timeout;

    manu_data[9] = _min(shot_ammo, 100); // limit to 0-100

    manu_data[10] = ( (practicing_channel << 4) & 0xF0 ) | ( playing_channel & 0x0F );

    manu_data[11] = (mqtt_game_id >> 24) & 0xFF;
    manu_data[12] = (mqtt_game_id >> 16) & 0xFF;
    manu_data[13] = (mqtt_game_id >> 8) & 0xFF;
    manu_data[14] = mqtt_game_id & 0xFF;

    manu_data[15] = mqtt_during_playing & 0x01; // limit to 0-1

    std::string s(reinterpret_cast<char const*>(manu_data), sizeof(manu_data));
    return s;
}


// our new MAC Address for BLE
// DEADBEEFCAFE
uint8_t newMACAddress[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE};
// if using esp_base_mac_addr_set(&newMACAddress[0]); newMACAddress should be 2 less
// uint8_t newMACAddress[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFC};

void printDeviceAddress() {
  const uint8_t* point = esp_bt_dev_get_address();
  for (int i = 0; i < 6; i++) {
    char str[3];
    sprintf(str, "%02X", (int)point[i]);
    Serial.print(str);
    if (i < 5){
      Serial.print(":");
    }
  }
  Serial.println("");
}

void printAdvData(std::string s) {
  for (int i = 0; i < s.size(); i++)
  {
    char str[3];
    sprintf(str, "%02X", (int)s.c_str()[i]);
    Serial.print(str);
    if (i< s.size()-1) {
      Serial.print(":");
    }
  }
  Serial.println("");

}

void setup() {
  Serial.begin(115200);

  // mac address should be 2 less (this also sets wifi mac)
  //esp_base_mac_addr_set(&newMACAddress[0]);


  // Create the BLE Device
  BLEDevice::init(""); // max 29 char

  // this prints the real device address, we set our custom address for the broadcast packets
  //printDeviceAddress();


  pinMode( BUTTON0_PIN, INPUT_PULLUP );
  pinMode( BUTTON1_PIN, INPUT_PULLUP );

  Serial.println("Waiting for button press...");
}

bool prestartCounting = false;
int64_t lastMicrosPrestart = 0;
const long prestartInterval = 1000000; // 1 second
int countdown_hiding_time = HIDING_TIME;
bool nextRound = false;
const long nextRoundInterval = 1000000; // 1 second
const int nextRoundRepeat = NEXT_ROUND_REPEAT;
int nextRoundRepeatCounter = nextRoundRepeat;

void init_prestart_countdown() {
  BLEDevice::stopAdvertising();
  countdown_hiding_time = HIDING_TIME;
  prestartCounting = false;
}

void init_next_round_countdown() {
  BLEDevice::stopAdvertising();
  nextRound = false;
  nextRoundRepeatCounter = nextRoundRepeat;
}

void loop() {
  //Serial.println("running loop");


  if (buttons.getButton(0)) {
    button0_pressed = true;
  }
  if (buttons.getButton(1)) {
    button1_pressed = true;
  }
  startMicros = esp_timer_get_time();

  if (button0_pressed) {
    init_next_round_countdown(); //stop the other function
    prestartCounting = true;
    button0_pressed = false;
  }

  if (button1_pressed) {
    init_prestart_countdown(); // stop the other function
    nextRound = true;
    button1_pressed = false;
  }

  if (prestartCounting) {
    
    if (startMicros - lastMicrosPrestart >= prestartInterval) {
      lastMicrosPrestart = startMicros;

      BLEDevice::stopAdvertising();

      Serial.print("countdown_hiding_time: ");
      Serial.print(countdown_hiding_time);
      Serial.print(" ");

      BLEAdvertisementData advertisementData = BLEAdvertisementData();
      std::string s = encodeManufacturerData(PRESTART_TYPE, countdown_hiding_time, PLAYING_TIME, HIT_DAMAGE, HIT_TIMEOUT, SHOT_AMMO, PRACTICING_CHANNEL, PLAYING_CHANNEL, MQTT_GAME_ID, MQTT_DURING_PLAYING);
      printAdvData(s);
      advertisementData.setManufacturerData(s);

      BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
      pAdvertising->setDeviceAddress(&newMACAddress[0]);
      pAdvertising->setAdvertisementType(ADV_TYPE_NONCONN_IND); //Non-Connectable Non-Scannable Undirected advertising
      pAdvertising->setScanResponse(false);
      pAdvertising->setMinInterval(0x0020); // Range: 0x0020 to 0x4000 Time = N * 0.625 msec Time Range: 20 ms to 10.24 sec
      pAdvertising->setMaxInterval(0x0020);
      pAdvertising->setAdvertisementData(advertisementData);
      
      BLEDevice::startAdvertising();

      if (countdown_hiding_time > 0) {
        countdown_hiding_time --;
      } else {
        init_prestart_countdown();
        Serial.println("Waiting for button press...");
      }
      
    }
  }

  if (nextRound) {
    if (startMicros - lastMicrosPrestart >= nextRoundInterval) {
      lastMicrosPrestart = startMicros;

      BLEDevice::stopAdvertising();

      Serial.print("nextRoundRepeatCounter: ");
      Serial.print(nextRoundRepeatCounter);
      Serial.print(" ");

      BLEAdvertisementData advertisementData = BLEAdvertisementData();
      std::string s = encodeManufacturerData(NEXT_ROUND_TYPE, HIDING_TIME, PLAYING_TIME, HIT_DAMAGE, HIT_TIMEOUT, SHOT_AMMO, PRACTICING_CHANNEL, PLAYING_CHANNEL, MQTT_GAME_ID, MQTT_DURING_PLAYING);
      printAdvData(s);
      advertisementData.setManufacturerData(s);

      BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
      pAdvertising->setDeviceAddress(&newMACAddress[0]);
      pAdvertising->setAdvertisementType(ADV_TYPE_NONCONN_IND); //Non-Connectable Non-Scannable Undirected advertising
      pAdvertising->setScanResponse(false);
      pAdvertising->setMinInterval(0x0020); // Range: 0x0020 to 0x4000 Time = N * 0.625 msec Time Range: 20 ms to 10.24 sec
      pAdvertising->setMaxInterval(0x0020);
      pAdvertising->setAdvertisementData(advertisementData);
      
      BLEDevice::startAdvertising();

      if (nextRoundRepeatCounter > 0) {
        nextRoundRepeatCounter --;
      } else {
        init_next_round_countdown();
        Serial.println("Waiting for button press...");
      }
    }    
  }


  delay(5); // slow the loop down, otherwise the esp32 becomes not responsive when broadcasting, why?


}
