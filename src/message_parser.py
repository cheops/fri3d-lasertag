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


def search(ble_msg, regexp, cast_type = None):
    found = regexp.search(ble_msg)
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

def parse_player_prestart_msg(ble_msg):
    #player_60HT_300PT_30HD_5HTO_0SA_2PRC_4PLC0374G
    parsed = {'type': search(ble_msg, c_type),
              'hiding_time': search(ble_msg, c_hiding_time, int),
              'playing_time': search(ble_msg, c_playing_time, int),
              'hit_damage': search(ble_msg, c_hit_damage, int),
              'hit_timeout': search(ble_msg, c_hit_timeout, int),
              'shot_ammo': search(ble_msg, c_shot_ammo, int),
              'playing_channel': search(ble_msg, c_playing_channel, int),
              'game_id': search(ble_msg, c_game_id),
              'mqtt_during_playing': search(ble_msg, c_mqtt_during_playing, str2bool)}
    return parsed


def parse_flag_prestart_msg(ble_msg):
    #flag_60HT_300PT_30HD_5HTO_2PRC_4PLC0374G
    parsed = {'type': search(ble_msg, c_type),
              'hiding_time': search(ble_msg, c_hiding_time, int),
              'playing_time': search(ble_msg, c_playing_time, int),
              'hit_damage': search(ble_msg, c_hit_damage, int),
              'hit_timeout': search(ble_msg, c_hit_timeout, int),
              'playing_channel': search(ble_msg, c_playing_channel, int),
              'game_id': search(ble_msg, c_game_id),
              'mqtt_during_playing': search(ble_msg, c_mqtt_during_playing, str2bool)}
    return parsed
