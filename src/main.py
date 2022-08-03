from mvp import states_mvp, transitions_mvp, BOOTING
from profiles_mvp import player_buzz_profile
from statemachine import StateMachine
from time import sleep
from effects import effect_star_wars, effect_clean

effect_star_wars()
sleep(0.5)
effect_clean()

mvp_statemachine = StateMachine(player_buzz_profile,
                                states_mvp,
                                transitions_mvp,
                                BOOTING)
mvp_statemachine.start()
