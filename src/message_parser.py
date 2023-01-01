import re

c_type = re.compile(r'(player|flag)_')
c_hiding_time = re.compile(r'([0-9]+)HT_')
c_playing_time = re.compile(r'([0-9]+)PT_')
c_hit_damage = re.compile(r'([0-9]+)HD_')
c_hit_timeout = re.compile(r'([0-9]+)HTO_')
c_shot_ammo = re.compile(r'([0-9]+)SA_')
c_practicing_channel = re.compile(r'([0-9]+)PRC_')
c_playing_channel = re.compile(r'([0-9]+)PLC_')
c_game_id = re.compile(r'([0-9]+)G_')
c_mqtt_during_playing = re.compile(r'(False|True)MQT_')


def str2bool(v):
    return v.lower() in ("yes", "true", "on", 1)


# 11 = length 17
# FF = type (0xFF Manufacturer Specific Data)
# - x bytes manufacturer specific data (max 29)
# - 2 bytes manufacturer UUID (set to 0xFF 0xFF)
# - y bytes custom data (max 27)
#
# we need to encode the x bytes manufacturer specific data (max 29)
# uint8_t message_type (1 byte 0-255)
# uint16_t hiding_time (2 bytes 0-65535) seconds
# uint16_t playing_time (2 bytes 0-65535) seconds
# uint8_t hit_damage (1 byte 0-100) health %
# uint8_t hit_timeout (1 byte 0-255) seconds
# uint8_t shot_ammo (1 byte 0-100) ammo %
# uint8_t practicing_channel (half byte 0-15) 0 is default channel, 3 is default practicing_channel
# uint8_t playing_channel (half byte 0-15) 0 is default channel, 4 is default playing_channel
# uint32_t game_id (4 bytes 0-4294967296)
# bool mqtt_during_playing (1 bit 0-1)


class BleMessage:
    def __init__(self, raw):
        assert len(raw) == 14
        self._raw = raw

    @classmethod
    def message_type_of_raw(cls, raw):
        return raw[0]

    @property
    def raw(self):
        return self._raw

    @property
    def message_type(self):
        return self._raw[0]

    @property
    def hiding_time(self):
        return self._raw[1]*256 + self._raw[2]

    @property
    def playing_time(self):
        return self._raw[3]*256 + self._raw[4]

    @property
    def hit_damage(self):
        return self._raw[5]

    @property
    def hit_timeout(self):
        return self._raw[6]

    @property
    def shot_ammo(self):
        return self._raw[7]

    @property
    def practicing_channel(self):
        return self._raw[8] >> 4

    @property
    def playing_channel(self):
        return self._raw[8] & 0x0F

    @property
    def game_id(self):
        return self._raw[9]*16777216 + self._raw[10]*65536 + self._raw[11]*256 + self._raw[12]

    @property
    def mqtt_during_playing(self):
        return bool(self._raw[13] & 0x01)

    def __repr__(self) -> str:
        return f"type:{self.message_type}, hiding_time:{self.hiding_time}, playing_time:{self.playing_time}"


def search(msg, regexp, cast_type=None):
    found = regexp.search(msg)
    if found is not None and found.group(1):
        if cast_type is not None:
            try:
                cast_value = cast_type(found.group(1))
                return cast_value
            except Exception as e:
                return None
        else:
            return found.group(1)
    else:
        return None


def parse_player_prestart_msg(msg):
    #player_60HT_300PT_30HD_5HTO_0SA_2PRC_4PLC0374G
    parsed = {'type': search(msg, c_type),
              'hiding_time': search(msg, c_hiding_time, int),
              'playing_time': search(msg, c_playing_time, int),
              'hit_damage': search(msg, c_hit_damage, int),
              'hit_timeout': search(msg, c_hit_timeout, int),
              'shot_ammo': search(msg, c_shot_ammo, int),
              'playing_channel': search(msg, c_playing_channel, int),
              'game_id': search(msg, c_game_id),
              'mqtt_during_playing': search(msg, c_mqtt_during_playing, str2bool)}
    return parsed


def parse_flag_prestart_msg(msg):
    #flag_60HT_300PT_30HD_5HTO_2PRC_4PLC0374G
    parsed = {'type': search(msg, c_type),
              'hiding_time': search(msg, c_hiding_time, int),
              'playing_time': search(msg, c_playing_time, int),
              'hit_damage': search(msg, c_hit_damage, int),
              'hit_timeout': search(msg, c_hit_timeout, int),
              'playing_channel': search(msg, c_playing_channel, int),
              'game_id': search(msg, c_game_id),
              'mqtt_during_playing': search(msg, c_mqtt_during_playing, str2bool)}
    return parsed
