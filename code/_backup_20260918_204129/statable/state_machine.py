# statable/state_machine.py
from typing import Dict, List, Optional
from .model import State, Event, Transition, RoleFunction


class StateMachine:
    def __init__(self):
        self.states: Dict[str, State] = {}
        self.events: Dict[str, Event] = {}
        self.transitions: List[Transition] = []
        self.role_functions: Dict[str, RoleFunction] = {}
        self.initial_state: Optional[str] = None

        # ★ Layer settings
        self.layer_priority: int = 5          # 実行Priority（1〜9）
        self.layer_description: str = ""      # 層のDescription（任意）
        self.layer_name: str = ""             # ★ 層名（例: "Driver"）

    def add_state(self, state: State):
        if state.name in self.states:
            raise ValueError(f"State '{state.name}' already exists")
        self.states[state.name] = state

    def add_event(self, event: Event):
        if event.name in self.events:
            raise ValueError(f"Event '{event.name}' already exists")
        self.events[event.name] = event

    def remove_event(self, name: str):
        if name in self.events:
            del self.events[name]
        self.transitions = [t for t in self.transitions if t.event != name]

    def add_transition(self, trans: Transition):
        if trans.source not in self.states:
            raise ValueError(f"Source state '{trans.source}' not defined")
        if trans.target and trans.target not in self.states:
            raise ValueError(f"Target state '{trans.target}' not defined")
        if trans.event and trans.event not in self.events:
            raise ValueError(f"Event '{trans.event}' not defined")
        self.transitions.append(trans)

    def remove_transition(self, trans: Transition):
        if trans in self.transitions:
            self.transitions.remove(trans)

    def set_initial(self, state_name: str):
        if state_name not in self.states:
            raise ValueError(f"State '{state_name}' not defined")
        self.initial_state = state_name

    def add_role_function(self, rf: RoleFunction):
        if rf.name in self.role_functions:
            raise ValueError(f"Role function '{rf.name}' already exists")
        self.role_functions[rf.name] = rf

    def remove_role_function(self, name: str):
        if name in self.role_functions:
            del self.role_functions[name]

    def get_transitions_for_cell(self, source: str, event: str) -> List[Transition]:
        return [t for t in self.transitions
                if t.source == source and t.event == event]

    def get_transitions_for_event(self, event: str) -> List[Transition]:
        return [t for t in self.transitions if t.event == event]