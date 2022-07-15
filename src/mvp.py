import statemachine

BOOTING = statemachine.State('booting')
PRACTICING = statemachine.State('practicing')
HIDING = statemachine.State('hiding')
PLAYING = statemachine.State('playing')
FINISHING = statemachine.State('finishing')

states_mvp = [BOOTING, PRACTICING, HIDING, PLAYING, FINISHING]

BOOT = statemachine.Event('boot')
CONFIRM_PROFILE = statemachine.Event('confirm_profile')
PRESTART = statemachine.Event('prestart')
COUNTDOWN_END = statemachine.Event('countdown_end')
DEAD = statemachine.Event('dead')

transitions_mvp = [
    statemachine.Transition(CONFIRM_PROFILE, BOOTING, PRACTICING),
    statemachine.Transition(PRESTART, PRACTICING, HIDING),
    statemachine.Transition(COUNTDOWN_END, HIDING, PLAYING),
    statemachine.Transition(COUNTDOWN_END, PLAYING, FINISHING),
    statemachine.Transition(DEAD, PLAYING, FINISHING),
    statemachine.Transition(BOOT, FINISHING, BOOTING),
]

hiding_time = 2 * 60
playing_time = 5 * 60
hit_damage = 5
hit_timeout = 3
