#ifndef BLASTER_HPP
#define BLASTER_HPP

#include <stdint.h>
#include "Arduino.h"
#include "blaster_packet.hpp"

// #define IR_RECEIVE_PIN 25  // IR receiver IO 25
#define BLASTER_LINK_PIN 4 // Blaster link IO 04

enum LinkState : uint8_t
{
    eLinkStateIdle = 0,
    eLinkStateReceiving = 1,
    eLinkStateSending = 2,
    eLinkStateWaitForAck = 3,
    eLinkStateWaitForAckReady = 4
};

volatile LinkState link_state = eLinkStateIdle;

enum ReaderState : uint8_t
{
    eReaderStateWaitForStart = 1,
    eReaderStateReadBits = 2,
    eReaderStateWaitForStop = 3,
    eReaderStateComplete = 4,
    eReaderStateError = 5
};

enum ReaderDecode : char
{
    eReaderDecodeStart = 'S',
    eReaderDecodeStop = 'P',
    eReaderDecodeOne = '1',
    eReaderDecodeZero = '0',
    eReaderDecodeUnknown = 'U'
};

static portMUX_TYPE my_spinlock = portMUX_INITIALIZER_UNLOCKED;

class BlasterReader
{
public:
    BlasterReader() {}

    static const int total_bits = 16;

    void reset()
    {
        m_state = eReaderStateWaitForStart;

        m_raw_data = 0;
        m_bits_read = 0;

        m_decoded_writer = 0;
        m_delta_writer = 0;
    }

    void move_to_buffer()
    {
        TimedRawData t;
        t.raw_data = m_raw_data;
        t.time_micros = esp_timer_get_time();
        m_buffer.add_message(t);

        m_stat_received += 1;

        reset();
    }

    /**
     * @brief process from the raw buffer and store valid messages in the message buffer.
     *        Also sets the ACK flag if an ack message was found
     */
    void process_buffer()
    {
        while (m_buffer.message_available())
        {
            DataPacket packet = DataPacket(m_buffer.pop_message());
            Serial.print("BLASTER_LINK: ");
            packet.print(&Serial);
            if (packet.calculate_crc() == packet.get_crc())
            {
                if (packet.get_command() == eCommandBlasterAck && packet.get_parameter() == eParameterBlasterNotReady)
                {
                    m_ack_state = true;
                    link_state = eLinkStateWaitForAckReady;
                }
                else if (packet.get_command() == eCommandBlasterAck && packet.get_parameter() == eParameterBlasterReady)
                {
                    m_ack_state = true;
                    link_state = eLinkStateIdle;
                }
                else if (packet.get_command() == eCommandTeamChange && packet.get_parameter() == eParameterTeamChangeHardware)
                {
                    m_hardware_team = packet.get_team();
                }
                else
                {
                    m_messages.add_message(packet);
                }
            }
            else
            {
                // crc failed
                m_stat_crc_failed += 1;
            }
        }
    }

    void save_deltas(bool save)
    {
        m_save_deltas = save;
    }

    void add_delta(int64_t delta)
    {
        if (m_save_deltas)
        {
            m_deltas[m_delta_writer] = delta;
            m_delta_writer += 1;
        }
    }

    void print_deltas(Print *aSerial)
    {
        if (m_save_deltas)
        {
            aSerial->print("deltas: ");
            for (uint8_t i = 0; i < m_delta_writer; i++)
            {
                aSerial->print(m_deltas[i]);
                if (i < m_delta_writer - 1)
                {
                    aSerial->print(", ");
                }
            }
            aSerial->println();
        }
    }

    void save_decoded(bool save)
    {
        m_save_decoded = save;
    }

    void add_decoded(char decoded)
    {
        if (m_save_decoded)
        {
            m_decoded[m_decoded_writer] = decoded;
            m_decoded_writer += 1;
        }
    }

    void print_decoded(Print *aSerial)
    {
        if (m_save_decoded)
        {
            aSerial->print("pa: ");
            for (uint8_t i = 0; i < m_decoded_writer; i++)
            {
                aSerial->print(m_decoded[i]);
                if (i < m_decoded_writer - 1)
                {
                    aSerial->print(", ");
                }
            }
            aSerial->println();
        }
    }

    // used for checking if a send was successful
    bool m_ack_state = false; // if an ACK was present in the last processed messages

    TeamColor m_hardware_team = eNoTeam;

    // to fetch the raw bits from the blaster-link
    ReaderState m_state = eReaderStateWaitForStart;
    int64_t m_ref_time = 0;
    uint16_t m_raw_data = 0;
    uint8_t m_bits_read = 0;

    uint16_t m_stat_received = 0;
    uint16_t m_stat_crc_failed = 0;

private:
    TimedRawDataRingBuffer m_buffer = TimedRawDataRingBuffer();

    DataPacketRingBuffer m_messages = DataPacketRingBuffer();

    // deltas can be used to debug the timings
    // saved for 1 packet
    bool m_save_deltas = false;
    int64_t m_deltas[total_bits + 2];
    uint8_t m_delta_writer = 0;

    // decoded contains deltas decoded to start, stop, 0, 1
    // saved for 1 packet
    bool m_save_decoded = false;
    char m_decoded[total_bits + 2];
    uint8_t m_decoded_writer = 0;
};

BlasterReader br = BlasterReader();

// timings JVC remote
// 1 packet: 1 start + 16 bits + stop
//
// 1 timeslot is 38kHz * 20 = 526us
//
// start = 16 high 8 low
// 1 = 1 high 3 low
// 0 = 1 high 1 low
// stop = 1 high 1 low
//
//*****************************************************************//
//             ISR                                                 //
// measure the timing between the RISING edges                     //
// when full JVC remote code is received, move it to buffer        //
//*****************************************************************//
void IRAM_ATTR handle_blaster_isr()
{
    int64_t t = esp_timer_get_time();

    link_state = eLinkStateReceiving;

    int64_t delta = t - br.m_ref_time;
    br.m_ref_time = t;

    ReaderDecode decoded = eReaderDecodeUnknown;

    if ((delta > 421) && (delta < 632)) // 1 timeslot 526 µs +/- 20% ==> stop
    {
        decoded = eReaderDecodeStop;
    }
    else if ((delta) > 840 && (delta < 1313)) // 2 timeslot 1052 µs +/- 20% ==> 0
    {
        decoded = eReaderDecodeZero;
        if (br.m_state == eReaderStateReadBits)
        {
            br.m_raw_data = br.m_raw_data >> 1;
            br.m_bits_read += 1;
        }
    }
    else if ((delta > 1680) && (delta < 2625)) // 4 timeslots 2100 µs +/- 20% ==> 1
    {
        decoded = eReaderDecodeOne;
        if (br.m_state == eReaderStateReadBits)
        {
            br.m_raw_data = (1 << 15) | (br.m_raw_data >> 1);
            br.m_bits_read += 1;
        }
    }
    else if (delta > 3789) // 8+1 timeslot 4737 µs - 20% ==> start
    {
        decoded = eReaderDecodeStart;
    }
    else
    {
        decoded = eReaderDecodeUnknown;
    }

    br.add_delta(delta);
    br.add_decoded(decoded);

    switch (br.m_state)
    {
    case eReaderStateWaitForStart:
        if (decoded == eReaderDecodeStart)
        {
            br.m_state = eReaderStateReadBits;
        }
        else
        {
            br.m_state = eReaderStateError;
        }
        break;
    case eReaderStateReadBits:
        if (decoded == eReaderDecodeOne || decoded == eReaderDecodeZero)
        {
            if (br.m_bits_read == br.total_bits)
            {
                br.m_state = eReaderStateWaitForStop;
            }
        }
        else
        {
            br.m_state = eReaderStateError;
        }
        break;
    case eReaderStateWaitForStop:
        if (decoded == eReaderDecodeStop)
        {
            br.m_state = eReaderStateComplete;
        }
        else
        {
            br.m_state = eReaderStateError;
        }
        break;
    } // switch

    if (br.m_state == eReaderStateError)
    {
        br.reset();
    }

    if (br.m_state == eReaderStateComplete)
    {
        br.move_to_buffer();
        link_state = eLinkStateIdle;
    }
}



class BlasterLink
{
public:
    BlasterLink() {}

    static void start_listen()
    {
        pinMode(BLASTER_LINK_PIN, INPUT_PULLUP);
        attachInterrupt(BLASTER_LINK_PIN, handle_blaster_isr, RISING);
    }

    static void stop_listen()
    {
        while (br.m_state != eReaderStateWaitForStart)
        {
            vTaskDelay(500 / portTICK_PERIOD_MS);
        }
        detachInterrupt(BLASTER_LINK_PIN);
    }

    static void process_buffer() {
        br.process_buffer();
    }

    /**
     * @brief Sets the IR channel (0..15).
     * Only blasters on the same IR channel can communicate via IR.
     *
     * @param channel_id the ir-channel to use
     * @return true setting channel acknowledged by blaster
     * @return false setting channel not acknowledged by blaster
     */
    static bool set_channel(uint8_t channel_id)
    {
        if (channel_id > 15)
            return false;

        DataPacket p = DataPacket();
        p.set_team(eNoTeam);
        p.set_trigger(false);
        p.set_command(eCommandSetChannel);
        p.set_parameter(channel_id);
        p.calculate_crc(true);

        bool success = send_to_blaster_retry(p.get_raw());
        return success;
    }

    /**
     * @brief Sets various trigger action flags
     * 
     * @param stealth silent shooting
     * @param single_shot only 1 shot allowed
     * @param healing true: healing shot, false damage shot
     * @param disable true: no shooting allowed, false shooting allowed (damage or healing)
     * @return true acknowledged by blaster
     * @return false not acknowledged by blaster
     */
    static bool set_trigger_action(bool stealth=false, bool single_shot=false, bool healing=false, bool disable=false) {
        DataPacket p = DataPacket();
        p.set_command(eCommandSetTriggerAction);
        uint8_t parameter = 0;
        if (disable) parameter += 1;
        if (healing) parameter += 2;
        if (single_shot) parameter += 4;
        if (stealth) parameter += 8;
        p.set_parameter(parameter);

        bool success = send_to_blaster_retry(p.get_raw());
        return success;
    }

    /**
     * @brief Sets and locks the blaster team
     * 
     * @param team 0 (eNoTeam): release team lock
     *             1..15: lock blaster team. When this is set the blaster team will be locked to this team.
     *                    This means that the hardware team switch is not working anymore.
     *                    The blaster team can still change when playing in zombi mode.
     * @return true acknowledged by blaster
     * @return false not acknowledged by blaster
     */
    static bool set_team(TeamColor team) {
        DataPacket p = DataPacket();
        p.set_command(eCommandTeamChange);
        p.set_team(team);
        bool success = send_to_blaster_retry(p.get_raw());
        return success;
    }

    /**
     * @brief Set the game mode
     *        Mode 0: Timeout mode. (Default)
     *                When this mode is set the blaster will go in timeout mode when being shot.
     *                After a set time the blaster will auto heal and can continue the game.
     *                If the blaster receives a healing shot this timeout can be shortened.
     *        Mode 1: Zombie mode
     *                In this mode the blaster team will change to the color of the team that shot it.
     *                The game is over when all players are of the same color.
     *        Mode 2: Sudden death mode
     *                The blaster is very weak and will stop working after being shot once.
     *                The winner is the last player with a working blaster
     * 
     * @param mode the GameMode
     * @return true acknowledged by blaster
     * @return false not acknowledged by blaster
     */
    bool set_game_mode(GameMode mode) {
        // TODO: check if team is changed to 0 on blaster when not set in this packet
        DataPacket p = DataPacket();
        p.set_command(eCommandSetGameMode);
        bool success = send_to_blaster_retry(p.get_raw());
        return success;
    }

    /**
     * @brief play an animation on the blaster
     * 
     * @param animation the animation to play
     * @return true acknowledged by blaster
     * @return false not acknowledged by blaster
     */
    bool play_animation(AnimationNames animation) {
        DataPacket p = DataPacket();
        p.set_command(eCommandPlayAnimation);
        bool success = send_to_blaster_retry(p.get_raw());
        return success;
    }

    /**
     * @brief Set the hit timeout: the timeout in seconds the blaster is not able to shoot or get shot
     * 
     * @param timeout in seconds
     * @return true acknowledged by blaster
     * @return false not acknowledged by blaster
     */
    bool set_hit_timeout(uint8_t timeout) {
        if (timeout > 15) return false;
        DataPacket p = DataPacket();
        p.set_command(eCommandSetHitTimeout);
        p.set_parameter(timeout);
        bool success = send_to_blaster_retry(p.get_raw());
        return success;
    }

    /**
     * @brief This is a gimmick and not a game mechanic
     *        When the badge sends this message to the blaster it initiates a blaster chatter session.
     *        The blaster that receives this message will start "talking" blaster language then transmit the chatter message over IR.
     *        Blasters who receive this message will also start "talking" and retransmitting.
     * 
     *        Every time a blaster retransmits a message is decreases the time to live field. When the TTL == 0 it will stop.
     *        A blaster will also ignore any packages with a higher TTL than the lowest TTL it has received until now.
     * 
     * @return true acknowledged by blaster
     * @return false not acknowledged by blaster
     */
    bool start_shatter() {
        DataPacket p = DataPacket();
        p.set_command(eCommandChatter);
        p.set_parameter(9);
        bool success = send_to_blaster_retry(p.get_raw());
        return success;
    }

private:

    static const uint16_t JVC_TIMESLOT_MICROS = 526; // timings JVC remote: 1 timeslot is 1 / 38kHz * 20 = 526us
    static const uint16_t ir_start_high_time = JVC_TIMESLOT_MICROS * 16;
    static const uint16_t ir_start_low_time = JVC_TIMESLOT_MICROS * 8;
    static const uint16_t ir_zero_high_time = JVC_TIMESLOT_MICROS * 1;
    static const uint16_t ir_zero_low_time = JVC_TIMESLOT_MICROS * 1;
    static const uint16_t ir_one_high_time = JVC_TIMESLOT_MICROS * 1;
    static const uint16_t ir_one_low_time = JVC_TIMESLOT_MICROS * 3;
    static const uint16_t ir_stop_high_time = JVC_TIMESLOT_MICROS * 1;
    static const uint16_t ir_stop_low_time = JVC_TIMESLOT_MICROS * 1;

    static bool send_to_blaster(uint16_t raw_data)
    {
        uint8_t waitCount = 0;
        while (link_state != eLinkStateIdle)
        {
            // minimal packet transmit time is 58 * 526us = 30508us
            // wait for half = 15ms
            Serial.print("send_to_blaster :: link not idle: ");
            Serial.println(link_state);
            vTaskDelay(15 / portTICK_PERIOD_MS);
            waitCount += 1;
            if (waitCount > 3)
            {
                Serial.println("send_to_blaster :: failed getting idle blaster link");
                return false;
            }
        }
        // stop listening on the blaster link, shared pin
        stop_listen();
        link_state = eLinkStateSending;

        // configure the pin for sending
        pinMode(BLASTER_LINK_PIN, OUTPUT);

        // initialize esp32 rmt
        rmt_obj_t *rmt_send = NULL;
        if ((rmt_send = rmtInit(BLASTER_LINK_PIN, RMT_TX_MODE, RMT_MEM_64)) == NULL)
        {
            Serial.println("send_to_blaster :: init sender failed");
            link_state = eLinkStateIdle;
            start_listen();
            return false;
        }

        // set timing interval to 1 microsecond
        const float one_micro_second_tick = 1000.0f;
        float realTick = rmtSetTick(rmt_send, one_micro_second_tick); // 1us tick
        if (realTick != one_micro_second_tick)
        {
            Serial.printf("send_to_blaster :: rmtSetTick failed expected: %fns realTick: %fns\n", one_micro_second_tick, realTick);
            rmtDeinit(rmt_send);
            link_state = eLinkStateIdle;
            start_listen();
            return false;
        }

        // prepare the data
        static const uint8_t NR_OF_ALL_BITS = 18; // 1 start + 16 bit data + 1 stop
        rmt_data_t ir_data[NR_OF_ALL_BITS];
        ir_data[0].duration0 = ir_start_high_time;
        ir_data[0].level0 = 1;
        ir_data[0].duration1 = ir_start_low_time;
        ir_data[0].level1 = 0;

        for (uint8_t i = 0; i < 16; i++)
        {
            if (bitRead(raw_data, i))
            {
                ir_data[1 + i].duration0 = ir_one_high_time;
                ir_data[1 + i].level0 = 1;
                ir_data[1 + i].duration1 = ir_one_low_time;
                ir_data[1 + i].level1 = 0;
            }
            else
            {
                ir_data[1 + i].duration0 = ir_zero_high_time;
                ir_data[1 + i].level0 = 1;
                ir_data[1 + i].duration1 = ir_zero_low_time;
                ir_data[1 + i].level1 = 0;
            }
        }
        ir_data[17].duration0 = ir_stop_high_time;
        ir_data[17].level0 = 1;
        ir_data[17].duration1 = ir_stop_low_time;
        ir_data[17].level1 = 0;

        // send the prepared data
        Serial.printf("send_to_blaster :: Sending data: %X\n", raw_data);
        bool success = rmtWriteBlocking(rmt_send, ir_data, NR_OF_ALL_BITS);
        if (!success)
        {
            Serial.println("send_to_blaster :: rmtWriteBlocking failed.");
            rmtDeinit(rmt_send);
            link_state = eLinkStateIdle;
            start_listen();
            return false;
        }

        // check for ACK within 100ms
        // const uint16_t BLASTER_ACK = 0xF0;
        // clear the br ack_state
        br.m_ack_state = false;

        // clean up the esp32 rmt
        rmtDeinit(rmt_send);

        // listen on the blaster link again
        link_state = eLinkStateWaitForAck;
        start_listen();

        // wait at least 100ms for Ack
        vTaskDelay(135 / portTICK_PERIOD_MS);
        br.process_buffer();
        if (br.m_ack_state != true)
        {
            Serial.println("send_to_blaster :: no Ack received.");
            link_state = eLinkStateIdle;
            return false;
        }
        else
        {
            if (link_state == eLinkStateWaitForAckReady)
            {
                Serial.println("send_to_blaster :: no Ack Ready received.");
                link_state = eLinkStateIdle;
            }
            return true;
        }
    }

    static bool send_to_blaster_retry(uint16_t raw_data, uint8_t retries = 3)
    {
        uint8_t retryCount = 0;
        while (retryCount < retries)
        {
            bool success = send_to_blaster(raw_data);
            if (!success)
            {
                retryCount += 1;
                vTaskDelay(50 * retryCount / portTICK_PERIOD_MS); // sleep
                Serial.printf("send_to_blaster :: retrying: %d\n", retryCount);
            }
            else
            {
                return true;
            }
        }
        return false;
    }
};

BlasterLink blasterLink = BlasterLink();

#endif