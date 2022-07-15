import statemachine
import mvp
import flag_buzz

mvp_statemachine = statemachine.StateMachine(flag_buzz.flag_buzz_profile,
                                             mvp.states_mvp,
                                             mvp.transitions_mvp,
                                             mvp.BOOTING)

