import st7789
import hardware

REX = 'REX'
GIGGLE = 'GIGGLE'
BUZZ = 'BUZZ'

teams = [REX, GIGGLE, BUZZ]

_color_rex = st7789.color565(255, 62, 62)
_color_giggle = st7789.color565(47, 173, 131)
_color_buzz = st7789.color565(62, 62, 255)

team_colors = {REX: _color_rex,
               GIGGLE: _color_giggle,
               BUZZ: _color_buzz}

team_blaster = {REX: hardware.blaster.Team.rex,
                GIGGLE: hardware.blaster.Team.giggle,
                BUZZ: hardware.blaster.Team.buzz}
