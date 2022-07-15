"""
inspiration from https://github.com/pytransitions
"""


class StateMachine:
    def __init__(self, model, states=None, transitions=None, initial=None):
        self.model = model
        self.states = [] if states is None else states
        self.transitions = [] if transitions is None else transitions
        self.state = initial
        self.model.run(self.state, self)

    def set_new_model(self, new_model):
        self.model = new_model

    def add_transition(self, trigger, source, dest):
        self.transitions.append(Transition(trigger, source, dest))

    def trigger(self, event):
        for t in self.transitions:
            if t.trigger.name == event.name and t.source.name == self.state.name:
                self.state = t.destination
                new_model = event.clear_new_model()
                if new_model:
                    self.model = new_model
                self.model.run(self.state, self)
                break


class State:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.__class__.__name__ + ':' + self.name


class Event:
    def __init__(self, name):
        self.name = name
        self._kv = {}

    def set_new_model(self, model):
        self._kv['new_model'] = model

    def clear_new_model(self):
        if 'new_model' in self._kv:
            return self._kv.pop('new_model')

    def __repr__(self):
        return self.__class__.__name__ + ':' + self.name


class Transition:
    def __init__(self, trigger, source, destination):
        self.trigger = trigger
        self.source = source
        self.destination = destination

    def __repr__(self):
        return self.__class__.__name__ + ':' + self.trigger + '=' + self.source + '->' + self.destination


# def test_it():
#     BOOTING = State('booting')
#     PRACTICING = State('practicing')
#     HIDING = State('hiding')
#     PLAYING = State('playing')
#     FINISHING = State('finishing')
#
#     states_mvp = [BOOTING, PRACTICING, HIDING, PLAYING, FINISHING]
#
#     BOOT = Event('boot')
#     CONFIRM_PROFILE = Event('confirm_profile')
#     PRESTART = Event('prestart')
#     START = Event('start')
#     END = Event('end')
#
#     transitions_mvp = [
#         Transition(CONFIRM_PROFILE, BOOTING, PRACTICING),
#         Transition(PRESTART, PRACTICING, HIDING),
#         Transition(START, HIDING, PLAYING),
#         Transition(END, PLAYING, FINISHING),
#         Transition(BOOT, FINISHING, BOOTING),
#     ]
#
#     class Player:
#         pass
#
#     player = Player()
#
#     statemachine_mvp = StateMachine(player, states_mvp, transitions_mvp, initial=BOOTING)
#
#     print(statemachine_mvp.state)
#     statemachine_mvp.trigger(CONFIRM_PROFILE)
#     print(statemachine_mvp.state)
#
#
# #test_it()
#

