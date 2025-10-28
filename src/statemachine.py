"""
inspiration from https://github.com/pytransitions
"""


class StateMachine:
    def __init__(self, model, states=None, transitions=None, initial=None):
        self.model = model
        self.states = [] if states is None else states
        self.transitions = [] if transitions is None else transitions
        self.state = initial

    def set_new_model(self, new_model):
        self.model = new_model

    def add_transition(self, trigger, source, dest):
        self.transitions.append(Transition(trigger, source, dest))

    # this is an async function that runs forever
    async def start(self):
        while True:
            new_event = await self.model.run(self.state)
            print("model run finished, new_event", new_event)
            for t in self.transitions:
                if t.trigger.name == new_event.name and t.source.name == self.state.name:
                    print("new_event:", new_event, "transition.source:", t.source, "transition.destination:", t.destination)
                    self.state = t.destination
                    new_model = new_event.clear_new_model()
                    if new_model:
                        self.model = new_model
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


if __name__ == "__main__":
    def test_it():
        import uasyncio

        BOOTING = State('booting')
        PRACTICING = State('practicing')
        HIDING = State('hiding')
        PLAYING = State('playing')
        FINISHING = State('finishing')

        states_mvp = [BOOTING, PRACTICING, HIDING, PLAYING, FINISHING]

        BOOT = Event('boot')
        CONFIRM_PROFILE = Event('confirm_profile')
        PRESTART = Event('prestart')
        START = Event('start')
        END = Event('end')

        transitions_mvp = [
            Transition(CONFIRM_PROFILE, BOOTING, PRACTICING),
            Transition(PRESTART, PRACTICING, HIDING),
            Transition(START, HIDING, PLAYING),
            Transition(END, PLAYING, FINISHING),
            Transition(BOOT, FINISHING, BOOTING),
        ]

        class Player:
            def __init__(self):
                self.event = None

            def set_event(self, event):
                self.event = event

            def run(self):

                while self.event is None:
                    uasyncio.sleep(1)
                return self.event

        player = Player()

        statemachine_mvp = StateMachine(player, states_mvp, transitions_mvp, initial=BOOTING)

        try:
            uasyncio.run(statemachine_mvp.start())
        finally:
            uasyncio.new_event_loop()  # Clear retained state


    test_it()

