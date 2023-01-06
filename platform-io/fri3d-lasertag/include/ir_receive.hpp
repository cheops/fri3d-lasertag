#ifndef IR_RECEIVE_HPP
#define IR_RECEIVE_HPP


#include "IrPinDefinitionsAndMore.h"
#include "IRremote.hpp"
#include <stdint.h>
#include "Arduino.h"
#include "blaster_packet.hpp"

class BadgeIrReceiver {
public:
    BadgeIrReceiver(){}

    void setup() {
        // setup ir receiver
        IrReceiver.begin(IR_RECEIVE_PIN);
    }

    void receive_ir_data() {
        if (IrReceiver.decode()) {
            int64_t time_micros = esp_timer_get_time(); // take time as soon as possible
            if (IrReceiver.decodedIRData.protocol == JVC) {
                m_stat_received += 1;
                TimedRawData t = TimedRawData();
                t.raw_data = IrReceiver.decodedIRData.decodedRawData;
                t.time_micros = time_micros;

                DataPacket packet = DataPacket(t);
                Serial.print("IR_RECEIVE_PIN: ");
                packet.print(&Serial);
                if (packet.calculate_crc() == packet.get_crc()) {
                    m_buffer.add_message(packet);
                } else {
                    // crc failed
                    m_stat_crc_failed += 1;
                }

            }

        IrReceiver.resume();
        }
    }
    uint16_t m_stat_received = 0;
    uint16_t m_stat_crc_failed = 0;
private:
    DataPacketRingBuffer m_buffer = DataPacketRingBuffer();

};

BadgeIrReceiver badgeIrReceiver = BadgeIrReceiver();

#endif