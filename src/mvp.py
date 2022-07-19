from statemachine import State, Event, Transition

BOOTING = State('booting')
PRACTICING = State('practicing')
HIDING = State('hiding')
PLAYING = State('playing')
FINISHING = State('finishing')

states_mvp = [BOOTING, PRACTICING, HIDING, PLAYING, FINISHING]

BOOT = Event('boot')
CONFIRM_PROFILE = Event('confirm_profile')
PRESTART = Event('prestart')
COUNTDOWN_END = Event('countdown_end')
DEAD = Event('dead')

transitions_mvp = [
    Transition(CONFIRM_PROFILE, BOOTING, PRACTICING),
    Transition(PRESTART, PRACTICING, HIDING),
    Transition(COUNTDOWN_END, HIDING, PLAYING),
    Transition(COUNTDOWN_END, PLAYING, FINISHING),
    Transition(DEAD, PLAYING, FINISHING),
    Transition(BOOT, FINISHING, BOOTING),
]

hiding_time = 10
playing_time = 10
hit_damage = 5
hit_timeout = 3
