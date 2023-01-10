#ifndef IR_RECEIVE_HPP
#define IR_RECEIVE_HPP


#include "IrPinDefinitionsAndMore.h"
#include "IRremote.hpp"
#include <stdint.h>
#include "Arduino.h"
#include "blaster_packet.hpp"

static portMUX_TYPE ir_receiver_buffer_spinlock = portMUX_INITIALIZER_UNLOCKED;

class BadgeIrReceiver {
public:
    BadgeIrReceiver(){}

    void setup() {
        // setup ir receiver
        IrReceiver.begin(IR_RECEIVE_PIN);
    }

    bool message_available() {
        taskENTER_CRITICAL(&ir_receiver_buffer_spinlock);
        bool available = m_buffer.message_available();
        taskEXIT_CRITICAL(&ir_receiver_buffer_spinlock);
        return available;
    }

    DataPacket pop_message() {
        taskENTER_CRITICAL(&ir_receiver_buffer_spinlock);
        DataPacket p = m_buffer.pop_message();
        taskEXIT_CRITICAL(&ir_receiver_buffer_spinlock);
        return p;
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
                //Serial.print("IR_RECEIVE_PIN: ");
                //packet.print(&Serial);
                if (packet.calculate_crc() == packet.get_crc()) {
                    taskENTER_CRITICAL(&ir_receiver_buffer_spinlock);
                    m_buffer.add_message(packet);
                    taskEXIT_CRITICAL(&ir_receiver_buffer_spinlock);
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