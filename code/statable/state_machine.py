from typing import Dict, List, Optional
from .model import State, Event, Transition


class StateMachine:
    def __init__(self):
        self.states: Dict[str, State] = {}
        self.events: Dict[str, Event] = {}
        self.transitions: List[Transition] = []
        self.initial_state: Optional[str] = None

    def add_state(self, state: State):
        if state.name in self.states:
            raise ValueError(f"State '{state.name}' already exists")
        self.states[state.name] = state

    def add_event(self, event: Event):
        if event.name in self.events:
            raise ValueError(f"Event '{event.name}' already exists")
        self.events[event.name] = event

    def add_transition(self, trans: Transition):
        if trans.source not in self.states:
            raise ValueError(f"Source state '{trans.source}' not defined")
        if trans.target and trans.target not in self.states:
            raise ValueError(f"Target state '{trans.target}' not defined")
        if trans.event and trans.event not in self.events:
            raise ValueError(f"Event '{trans.event}' not defined")
        self.transitions.append(trans)

    def set_initial(self, state_name: str):
        if state_name not in self.states:
            raise ValueError(f"State '{state_name}' not defined")
        self.initial_state = state_name