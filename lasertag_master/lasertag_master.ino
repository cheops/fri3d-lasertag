#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Fri3dButtons.h>

#define HIDING_TIME 10
#define PLAYING_TIME 30
#define HIT_DAMAGE 5
#define HIT_TIMEOUT 3
#define SHOT_AMMO 0
#define PLAYING_CHANNEL 4
#define GAME_ID 1234
#define MQTT_DURING_PLAYING "False"

Fri3dButtons buttons = Fri3dButtons();

BLEServer* pServer = NULL;
BLECharacteristic* pPrestartFlagCharacteristic = NULL;
BLECharacteristic* pPrestartPlayerCharacteristic = NULL;
BLECharacteristic* pNextRoundCharacteristic = NULL;
bool newDeviceConnectedToHandle = false;
bool button0_pressed = false;
bool button1_pressed = false;

long long startMicros = esp_timer_get_time();

#define LASERTAG_SERVICE_UUID        "936b"
#define PRESTART_FLAG_CHARACTERISTIC_UUID "c20a"
#define PRESTART_PLAYER_CHARACTERISTIC_UUID "c20b"
#define NEXT_ROUND_CHARACTERISTIC_UUID "c20c"

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      Serial.println("MyServerCallbacks onConnect");
      //BLEDevice::startAdvertising(); // if a client connects, advertising normally stops, so start it again
      //^done in loop
      newDeviceConnectedToHandle = true;
    };

    void onDisconnect(BLEServer* pServer) {
      Serial.println("MyServerCallbacks onDisconnect");
    }
};



void setup() {
  Serial.begin(115200);

  // Create the BLE Device
  BLEDevice::init("lasertag_master"); // max 29 char
  uint16_t mtu = 517;
  BLEDevice::setMTU(mtu);

  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pLasertagService = pServer->createService(LASERTAG_SERVICE_UUID);


  // Create a BLE Characteristic
  pPrestartFlagCharacteristic = pLasertagService->createCharacteristic(
                      PRESTART_FLAG_CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
                    );
  // Create a BLE Descriptor
  pPrestartFlagCharacteristic->addDescriptor(new BLE2902());


  // Create a BLE Characteristic
  pPrestartPlayerCharacteristic = pLasertagService->createCharacteristic(
                      PRESTART_PLAYER_CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
                    );
  // Create a BLE Descriptor
  pPrestartPlayerCharacteristic->addDescriptor(new BLE2902());


  // Create a BLE Characteristic
  pNextRoundCharacteristic = pLasertagService->createCharacteristic(
                      NEXT_ROUND_CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
                    );
  // Create a BLE Descriptor
  pNextRoundCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pLasertagService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(LASERTAG_SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);  // set value to 0x00 to not advertise this parameter
  BLEDevice::startAdvertising();

  pinMode( BUTTON0_PIN, INPUT_PULLUP );
  pinMode( BUTTON1_PIN, INPUT_PULLUP );

  Serial.println("Waiting a client connection to notify...");
}

bool prestartCounting = false;
long long lastMicrosPrestart = 0;
const long prestartInterval = 1000000; // 1 second
int countdown_hiding_time = HIDING_TIME;
bool nextRound = false;
const long nextRoundInterval = 1000000; // 1 second
const int nextRoundRepeat = 60;
int nextRoundRepeatCounter = nextRoundRepeat;

void init_prestart_countdown() {
  countdown_hiding_time = HIDING_TIME;
  prestartCounting = false;
}

void init_next_round_countdown() {
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
    init_next_round_countdown();
    prestartCounting = true;
    button0_pressed = false;
  }

  if (button1_pressed) {
    init_prestart_countdown();
    nextRound = true;
    button1_pressed = false;
  }

  if (prestartCounting) {
    
    if (startMicros - lastMicrosPrestart >= prestartInterval) {
      lastMicrosPrestart = startMicros;

      //Serial.print("countdown_hiding_time: ");
      //Serial.println(countdown_hiding_time);
      char buffer[60];
      sprintf(buffer, "player_%dHT_%dPT_%dHD_%dHTO_%dSA_%dPLC_%d4G_%sMQT_", 
        countdown_hiding_time, PLAYING_TIME, 
        HIT_DAMAGE, HIT_TIMEOUT, SHOT_AMMO,
        PLAYING_CHANNEL,
        GAME_ID,
        MQTT_DURING_PLAYING);
      pPrestartPlayerCharacteristic->setValue(buffer);
      pPrestartPlayerCharacteristic->notify();
      delay(10);
      Serial.println(buffer);

      sprintf(buffer, "flag_%dHT_%dPT_%dHD_%dHTO_%dPLC_%d4G_%sMQT_", 
        countdown_hiding_time, PLAYING_TIME, 
        HIT_DAMAGE, HIT_TIMEOUT, 
        PLAYING_CHANNEL,
        GAME_ID,
        MQTT_DURING_PLAYING);
      pPrestartFlagCharacteristic->setValue(buffer);
      pPrestartFlagCharacteristic->notify();
      delay(10);
      Serial.println(buffer);

      if (countdown_hiding_time > 0) {
        countdown_hiding_time --;
      } else {
        init_prestart_countdown();
      }
      
    }
  }

  if (nextRound) {
    if (startMicros - lastMicrosPrestart >= nextRoundInterval) {
      lastMicrosPrestart = startMicros;
      pNextRoundCharacteristic->setValue("next_round");
      pNextRoundCharacteristic->notify();
      delay(10);

      Serial.print("nextRoundRepeatCounter: ");
      Serial.print(nextRoundRepeatCounter);
      Serial.println(" next_round");

      if (nextRoundRepeatCounter > 0) {
        nextRoundRepeatCounter --;
      } else {
        init_next_round_countdown();
      }
    }    
  }


  // connecting: if a client connects, advertising normally stops, so start it again
  if (newDeviceConnectedToHandle) {
    Serial.println("client connected, restart advertising, so more clients can connect");
    BLEDevice::startAdvertising(); // restart advertising
    newDeviceConnectedToHandle = false;
  }

}
