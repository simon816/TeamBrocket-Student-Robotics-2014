"""
    This file is part of Team Brocket Robotics, licensed under the MIT License.
    A copy of the MIT License can be found in LICENSE.txt
"""

class State(object):
    def __init__(self, name):
        self.name = name
        self.listeners = []
        self.count = [0, 0, 0]
        self.was_interrupted = False
    def bind(self, action):
        if hasattr(action, '__call__'):
            self.listeners.append(action)
            return self
        raise TypeError("Callback is not callable")
    def action(self, host, *args):
        self.was_interrupted = False
        errors = []
        for listener in self.listeners:
            try:
                listener(*args)
                self.count[0] += 1
            except StateInterrupt as si:
                self.was_interrupted = True
                host.notify_handler('interrupt', [self, si])
                self.count[2] += 1
            except Exception as e:
                errors.append({'listener':listener, 'exception':e})
                self.count[1] += 1
        if len(errors) > 0:
            host.notify_handler('error', [self, errors])
            host.active_state = None
        else:
            host.state_finished(self)
    def __str__(self):
        return "<State %r [L:%d,C:%d,E:%d,I:%d]>" % (
            self.name, len(self.listeners), self.count[0], self.count[1],
            self.count[2])
    def __repr__(self):
        return str(self)

class StateRegister:
    def __init__(self):
        self.states = [[], {}]
    def register_state(self, state):
        if isinstance(state, State):
            self.states[0].append(state)
            self.states[1][state.name] = state
    def get_state(self, name):
        return self.states[1][name]
    def get_state_id(self, name):
        return self.states[0].index(self.states[1][name])
    def bind_states(self, state_dict):
        for name, func in state_dict.iteritems():
            self.get_state(name).bind(func)

class StateObserver:
    def __init__(self, stateregister):
        self.handlers = []
        self.register = stateregister
        self.active_state = None

    def bind(self, event, callback):
        if event in ['change', 'finish', 'error', 'interrupt']:
            self.handlers.append((event, callback))

    def get_register(self):
        return self.register

    def notify_handler(self, event, args=[]):
        for h in self.handlers:
            if h[0] == event:
                try:
                    h[1].__call__(*args)
                except Exception, e:
                    print e

    def change_state(self, state):
        state.action(self, *self.active_state_args)

    def set_state(self, name, args=[]):
        state = self.register.get_state(name)
        self.notify_handler('change', [self.active_state, state])
        if self.active_state is not None:
            self.notify_handler('finish', [self.active_state])
            print "[SM] State replaced"
        self.active_state = state
        self.active_state_args = args

    def state_finished(self, state):
        if state == self.active_state and not state.was_interrupted:
            self.notify_handler('finish', [state])
            self.active_state = None

    def get_active_state(self):
        return self.active_state

    def next_state(self):
        while self.active_state != None:
            yield self.active_state

    def get_states(self):
        return self.register.states[0]

class StateInterrupt(Exception):
    def __init__(self, id, args):
        self.id = id
        self.args = args

def StateMachine(states_dict):
    register = StateRegister()
    for name, fn in states_dict.iteritems():
        register.register_state(State(name).bind(fn))
    return StateObserver(register)
    