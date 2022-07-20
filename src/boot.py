from mvp import states_mvp, transitions_mvp, BOOTING
from profiles_mvp import player_buzz_profile
from statemachine import StateMachine

mvp_statemachine = StateMachine(player_buzz_profile,
                                states_mvp,
                                transitions_mvp,
                                BOOTING)
mvp_statemachine.start()
