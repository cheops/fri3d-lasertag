#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Fri3dButtons.h>

Fri3dButtons buttons = Fri3dButtons();

BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;
uint32_t value = 0;

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/

//#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
//#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

#define SERVICE_UUID        "936b"
#define CHARACTERISTIC_UUID "c20a"

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      BLEDevice::startAdvertising();
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
    }
};



void setup() {
  Serial.begin(115200);

  // Create the BLE Device
  BLEDevice::init("ESP32");
  uint16_t mtu = 128;
  BLEDevice::setMTU(128);

  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create a BLE Characteristic
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ   |
                      BLECharacteristic::PROPERTY_WRITE  |
                      BLECharacteristic::PROPERTY_NOTIFY |
                      BLECharacteristic::PROPERTY_INDICATE
                    );

  // https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.descriptor.gatt.client_characteristic_configuration.xml
  // Create a BLE Descriptor
  pCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);  // set value to 0x00 to not advertise this parameter
  BLEDevice::startAdvertising();

  pinMode( BUTTON0_PIN, INPUT_PULLUP );
  pinMode( BUTTON1_PIN, INPUT_PULLUP );
  
  Serial.println("Waiting a client connection to notify...");
}

void loop() {
    // notify changed value
    if (deviceConnected) {
        // pCharacteristic->setValue((uint8_t*)&value, 4);
        Serial.println("Waiting for button press...");
        
        while (!buttons.getButton(0)) {};

        Serial.println("Send start...");

        for (int countdown = 120; countdown >= 1; countdown--) {
          char buffer[40];
          sprintf(buffer, "<%dHT_300PT_30HD_", countdown);

          //pCharacteristic->setValue("<" + countdown + "HT_300PT_30HD_");
          pCharacteristic->setValue(buffer);
          pCharacteristic->notify();
          delay(10);
          pCharacteristic->setValue("5HTO_0SA_4PLC");
          pCharacteristic->notify();
          delay(10);
          pCharacteristic->setValue("_0374G_FalseMQT_>");
          pCharacteristic->notify();
          delay(1000);

          
          Serial.print("Countdown: ");
          Serial.println(countdown);
          delay(1000);
        }

        while (!buttons.getButton(1)) {};
            
        Serial.println("Send finish...");
        pCharacteristic->setValue("finish");
        pCharacteristic->notify();

        // value++;
        // delay(10); // bluetooth stack will go into congestion, if too many packets are sent, in 6 hours test i was able to go as low as 3ms
    }
    // disconnecting
    if (!deviceConnected && oldDeviceConnected) {
        delay(500); // give the bluetooth stack the chance to get things ready
        pServer->startAdvertising(); // restart advertising
        Serial.println("start advertising");
        oldDeviceConnected = deviceConnected;
    }
    // connecting
    if (deviceConnected && !oldDeviceConnected) {
        // do stuff here on connecting
        oldDeviceConnected = deviceConnected;
        Serial.println("Send stop...");
        
        pCharacteristic->setValue("stop");
        pCharacteristic->notify();
    }
}
