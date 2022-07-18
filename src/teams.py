import st7789py as st7789
from hardware import blaster

REX = 'REX'
GIGGLE = 'GIGGLE'
BUZZ = 'BUZZ'

teams = [REX, GIGGLE, BUZZ]

_color_rex = st7789.color565(255, 0, 0)
_color_giggle = st7789.color565(0, 140, 0)
_color_buzz = st7789.color565(0, 0, 210)

team_colors = {REX: _color_rex,
               GIGGLE: _color_giggle,
               BUZZ: _color_buzz}

team_blaster = {REX: blaster.Team.rex,
                GIGGLE: blaster.Team.giggle,
                BUZZ: blaster.Team.buzz}
