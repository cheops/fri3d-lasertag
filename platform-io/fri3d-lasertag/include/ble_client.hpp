#ifndef BLE_CLIENT_HPP
#define BLE_CLIENT_HPP

#include <stdint.h>
#include "Arduino.h"

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

enum BleMessageType : uint8_t
{
  eBleMessageTypeNone = 0,
  eBleMessageTypePrestart = 1,
  eBleMessageTypeNextRound = 2,
};

/**
 * @brief class to contain the manufacturer specific data
 * 
 * packet bytes explained
 * # 11 = length 17
 * # FF = type (0xFF Manufacturer Specific Data)
 * # - x bytes manufacturer specific data (max 29)
 * # - 2 bytes manufacturer UUID (set to 0xFF 0xFF)
 * # - y bytes custom data (max 27)
 * #
 * # we need to encode the x bytes manufacturer specific data (max 29)
 * # uint8_t message_type (1 byte 0-255)
 * # uint16_t hiding_time (2 bytes 0-65535) seconds
 * # uint16_t playing_time (2 bytes 0-65535) seconds
 * # uint8_t hit_damage (1 byte 0-100) health %
 * # uint8_t hit_timeout (1 byte 0-255) seconds
 * # uint8_t shot_ammo (1 byte 0-100) ammo %
 * # uint8_t practicing_channel (half byte 0-15) 0 is default channel, 3 is default practicing_channel
 * # uint8_t playing_channel (half byte 0-15) 0 is default channel, 4 is default playing_channel
 * # uint32_t game_id (4 bytes 0-4294967296)
 * # bool mqtt_during_playing (1 bit 0-1)
 * 
 */
class BleMessage {
public:
    BleMessage() {}
    BleMessage(std::string man_spec_data) {
        if (man_spec_data.size() != 13) Serial.printf("wrong length of man_spec_data: '%s'\n", man_spec_data);

        m_man_spec_data = man_spec_data.substr(0,13);
    }

    static BleMessageType get_message_type(std::string man_spec_data) {
        return BleMessageType(man_spec_data.at(0));
    }

    BleMessageType get_message_type() {
        return BleMessageType(m_man_spec_data[0]);
    }

    uint16_t get_hiding_time() {
        return m_man_spec_data[1]*256 + 
               m_man_spec_data[2];
    }

    uint16_t get_playing_time() {
        return m_man_spec_data[3]*256 + 
               m_man_spec_data[4];
    }

    uint8_t get_hit_damaage() {
        return m_man_spec_data[5];
    }

    uint8_t get_hit_timeout() {
        return m_man_spec_data[6];
    }

    uint8_t get_shot_ammo() {
        return m_man_spec_data[7];
    }

    uint8_t get_practicing_channel() {
        return m_man_spec_data[8] >> 4;
    }

    uint8_t get_playing_channel() {
        return m_man_spec_data[8] & 0x0F;
    }

    uint32_t get_game_id() {
    return m_man_spec_data[9]*16777216 + 
           m_man_spec_data[10]*65536 + 
           m_man_spec_data[11]*256 + 
           m_man_spec_data[12];
    }

    bool get_mqtt_during_playing() {
        return bool(m_man_spec_data[13] & 0x01);
    }

    void print(Print *aSerial) {
        aSerial->print("BleMessage: ");
        aSerial->print("type:");
        aSerial->print(get_message_type());
        aSerial->print(", hiding_time:");
        aSerial->print(get_hiding_time());
        aSerial->print(", playing_time:");
        aSerial->print(get_playing_channel());
        aSerial->print(", hit_damage:");
        aSerial->print(get_hit_damaage());
        aSerial->print(", hit_timeout");
        aSerial->print(get_hit_timeout());
        aSerial->print(", shot_ammo");
        aSerial->print(get_shot_ammo());
        aSerial->print(", practicing_channel");
        aSerial->print(get_practicing_channel());
        aSerial->print(", playing_channel");
        aSerial->print(get_playing_channel());
        aSerial->print(", game_id");
        aSerial->print(get_game_id());
        aSerial->print(", mqtt_during_playing");
        aSerial->print(get_mqtt_during_playing());
        aSerial->println();
    }

private:
    std::string m_man_spec_data;
};


void scanCompleteCB(BLEScanResults scanResults);

class BleClient: public BLEAdvertisedDeviceCallbacks {
public:
    BleClient(){}
    
    void start_scan() {
        bool success = m_pBLEScan->start(scanTime, scanCompleteCB, false);
        if (!success) Serial.println("Failed BLEScan->start()");
        m_listening = true;
    }

    void start_listen(BleMessageType listenType) {
        m_listen_type = listenType;

        BLEDevice::init("");
        m_pBLEScan = BLEDevice::getScan(); //create new scan
        m_pBLEScan->setAdvertisedDeviceCallbacks(this); // calls this.onResult()
        m_pBLEScan->setInterval(120); //ms
        m_pBLEScan->setWindow(30); // ms

        start_scan();
    }

    bool listen_type_found() {
        return !m_listening && m_bleMessage.get_message_type() == m_listen_type;
    }

    BleMessage get_ble_message() {
        return m_bleMessage;
    }

    void reset() {
        m_listen_type = eBleMessageTypeNone;
        m_bleMessage = BleMessage();
    }

private:
    static const int scanTime = 2; //In seconds
    bool m_listening = false;
    BLEScan* m_pBLEScan = NULL;
    BleMessage m_bleMessage = BleMessage();
    BleMessageType m_listen_type = eBleMessageTypeNone;

    void stop_listen() {
        m_pBLEScan->clearResults();   // delete results fromBLEScan buffer to release memory
        m_pBLEScan->stop();
        BLEDevice::deinit();
        m_listening = false;
    }

    // BLEAdvertisedDeviceCallbacks::onResult
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        Serial.printf("Advertised Device: %s \n", advertisedDevice.toString().c_str());
        esp_ble_addr_type_t addr_type = advertisedDevice.getAddressType();
        Serial.print("addr_type:");
        Serial.println(addr_type);

        BLEAddress addr = advertisedDevice.getAddress();
        Serial.print("addr:");
        Serial.println(addr.toString().c_str());

        std::string man_data = advertisedDevice.getManufacturerData();
        Serial.print("man_data:");
        Serial.println(man_data.c_str());

        std::string man_id = man_data.substr(0,2);
        Serial.print("man_id:");
        Serial.println(man_id.c_str());

        std::string man_spec_data = man_data.substr(2);
        Serial.print("man_spec_data:");
        Serial.println(man_spec_data.c_str());

        BleMessageType message_type = BleMessage::get_message_type(man_spec_data);
        Serial.print("message_type:");
        Serial.println(message_type);

        //m_bleMessage = BleMessage(man_spec_data);

        //stop_listen();

    }



};

BleClient bleClient = BleClient();

void scanCompleteCB(BLEScanResults scanResults) {
    // scan completed, but nothing found
    if (!bleClient.listen_type_found()) {
        //sleep a bit to go easy on ble
        delay(1000);
        bleClient.start_scan();
    }
}


#endif