
#ifndef IR_PIN_DEFINITIONS_AND_MORE_H
#define IR_PIN_DEFINITIONS_AND_MORE_H

//#define TRACE
//#define DEBUG

/*
 * - RAW_BUFFER_LENGTH                  Buffer size of raw input buffer. Must be even! 100 is sufficient for *regular* protocols of up to 48 bits.
 * - IR_SEND_PIN                        If specified (as constant), reduces program size and improves send timing for AVR.
 * - SEND_PWM_BY_TIMER                  Disable carrier PWM generation in software and use (restricted) hardware PWM.
 * - USE_NO_SEND_PWM                    Use no carrier PWM, just simulate an **active low** receiver signal. Overrides SEND_PWM_BY_TIMER definition.
 * - USE_OPEN_DRAIN_OUTPUT_FOR_SEND_PIN Use or simulate open drain output mode at send pin. Attention, active state of open drain is LOW, so connect the send LED between positive supply and send pin!
 * - EXCLUDE_EXOTIC_PROTOCOLS           If activated, BOSEWAVE, WHYNTER and LEGO_PF are excluded in decode() and in sending with IrSender.write().
 * - EXCLUDE_UNIVERSAL_PROTOCOLS        If activated, the universal decoder for pulse distance protocols and decodeHash (special decoder for all protocols) are excluded in decode().
 * - DECODE_*                           Selection of individual protocols to be decoded. See below.
 * - MARK_EXCESS_MICROS                 Value is subtracted from all marks and added to all spaces before decoding, to compensate for the signal forming of different IR receiver modules.
 * - RECORD_GAP_MICROS                  Minimum gap between IR transmissions, to detect the end of a protocol.
 * - FEEDBACK_LED_IS_ACTIVE_LOW         Required on some boards (like my BluePill and my ESP8266 board), where the feedback LED is active low.
 * - NO_LED_FEEDBACK_CODE               This completely disables the LED feedback code for send and receive.
 * - IR_INPUT_IS_ACTIVE_HIGH            Enable it if you use a RF receiver, which has an active HIGH output signal.
 * - IR_SEND_DUTY_CYCLE_PERCENT         Duty cycle of IR send signal.
 * - MICROS_PER_TICK                    Resolution of the raw input buffer data. Corresponds to 2 pulses of each 26.3 us at 38 kHz.
 * - IR_USE_AVR_TIMER*                  Selection of timer to be used for generating IR receiving sample interval.
 * 
 * 
 */
#define DECODE_JVC

#define EXCLUDE_UNIVERSAL_PROTOCOLS // Saves up to 1000 bytes program memory.
#define EXCLUDE_EXOTIC_PROTOCOLS
#define NO_LED_FEEDBACK_CODE // saves 500 bytes program memory

#define IR_RECEIVE_PIN 25  // IR receiver IO 25

#define SEND_PWM_BY_TIMER

#endif