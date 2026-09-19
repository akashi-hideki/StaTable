# statable/state_machine.py
from typing import Dict, List, Optional, Tuple

from .model import (
    State, Event, Transition, RoleFunction,
    ActionStep, TransitionRelation,
)


class StateMachine:
    def __init__(self):
        self.states: Dict[str, State] = {}
        self.events: Dict[str, Event] = {}
        self.transitions: List[Transition] = []
        self.role_functions: Dict[str, RoleFunction] = {}
        self.initial_state: Optional[str] = None

        # Layer settings
        self.layer_priority: int = 5
        self.layer_description: str = ""
        self.layer_name: str = ""

        # === v2.2: per-cell metadata ===
        # Key: (source_state_name, event_name)
        # Note: event_name may be "" for completion transitions.
        self.cell_actions: Dict[Tuple[str, str], List[ActionStep]] = {}
        self.cell_relations: Dict[Tuple[str, str], List[TransitionRelation]] = {}

    # ------------------------------------------------------------------
    # Existing API (unchanged)
    # ------------------------------------------------------------------
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
        # v2.2: drop cell metadata that referenced this event
        for key in [k for k in self.cell_actions if k[1] == name]:
            del self.cell_actions[key]
        for key in [k for k in self.cell_relations if k[1] == name]:
            del self.cell_relations[key]

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

    # ------------------------------------------------------------------
    # v2.2: cell action / relation accessors
    # ------------------------------------------------------------------
    def get_actions_for_cell(self, source: str, event: str) -> List[ActionStep]:
        return self.cell_actions.get((source, event), [])

    def set_actions_for_cell(self, source: str, event: str,
                              actions: List[ActionStep]) -> None:
        key = (source, event)
        if actions:
            self.cell_actions[key] = list(actions)
        else:
            self.cell_actions.pop(key, None)

    def get_relations_for_cell(self, source: str, event: str
                                ) -> List[TransitionRelation]:
        return self.cell_relations.get((source, event), [])

    def set_relations_for_cell(self, source: str, event: str,
                                relations: List[TransitionRelation]) -> None:
        key = (source, event)
        if relations:
            self.cell_relations[key] = list(relations)
        else:
            self.cell_relations.pop(key, None)

    def get_cell_keys(self) -> List[Tuple[str, str]]:
        """All (source, event) keys that have actions or relations."""
        keys = set(self.cell_actions.keys()) | set(self.cell_relations.keys())
        return sorted(keys)

    def remove_cell_metadata(self, source: str, event: str) -> None:
        """Remove all cell-level actions / relations for the given cell."""
        key = (source, event)
        self.cell_actions.pop(key, None)
        self.cell_relations.pop(key, None)