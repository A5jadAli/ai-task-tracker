"""
State machine for tracking execution state.
Ensures proper sequencing and prevents inconsistent states.
"""

from enum import Enum
from typing import Dict, Callable, Any, List
from datetime import datetime
import json


class ExecutionState(Enum):
    """Possible execution states."""

    INITIALIZED = "initialized"
    PLANNING = "planning"
    READY = "ready"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StateTransition:
    """Represents a state transition."""

    def __init__(
        self,
        from_state: ExecutionState,
        to_state: ExecutionState,
        condition: Callable = None,
        on_transition: Callable = None,
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition or (lambda: True)
        self.on_transition = on_transition or (lambda: None)
        self.timestamp = None

    def is_valid(self) -> bool:
        """Check if transition is valid."""
        return self.condition()

    def execute(self):
        """Execute transition callback."""
        self.timestamp = datetime.now()
        self.on_transition()


class StateMachine:
    """State machine for execution flow."""

    def __init__(self, initial_state: ExecutionState = ExecutionState.INITIALIZED):
        self.current_state = initial_state
        self.history: List[ExecutionState] = [initial_state]
        self.transitions: Dict[ExecutionState, List[StateTransition]] = {}
        self.metadata: Dict[str, Any] = {}
        self.setup_transitions()

    def setup_transitions(self):
        """Setup valid state transitions."""
        # From INITIALIZED
        self.add_transition(
            ExecutionState.INITIALIZED,
            ExecutionState.PLANNING,
            on_transition=lambda: self._log("Starting planning phase"),
        )

        # From PLANNING
        self.add_transition(
            ExecutionState.PLANNING,
            ExecutionState.READY,
            on_transition=lambda: self._log("Plan ready"),
        )
        self.add_transition(
            ExecutionState.PLANNING,
            ExecutionState.FAILED,
            on_transition=lambda: self._log("Planning failed"),
        )

        # From READY
        self.add_transition(
            ExecutionState.READY,
            ExecutionState.EXECUTING,
            on_transition=lambda: self._log("Starting execution"),
        )
        self.add_transition(
            ExecutionState.READY,
            ExecutionState.CANCELLED,
            on_transition=lambda: self._log("Execution cancelled"),
        )

        # From EXECUTING
        self.add_transition(
            ExecutionState.EXECUTING,
            ExecutionState.VERIFYING,
            on_transition=lambda: self._log("Verifying results"),
        )
        self.add_transition(
            ExecutionState.EXECUTING,
            ExecutionState.PAUSED,
            on_transition=lambda: self._log("Execution paused"),
        )
        self.add_transition(
            ExecutionState.EXECUTING,
            ExecutionState.FAILED,
            on_transition=lambda: self._log("Execution failed"),
        )

        # From PAUSED
        self.add_transition(
            ExecutionState.PAUSED,
            ExecutionState.EXECUTING,
            on_transition=lambda: self._log("Execution resumed"),
        )
        self.add_transition(
            ExecutionState.PAUSED,
            ExecutionState.CANCELLED,
            on_transition=lambda: self._log("Execution cancelled from pause"),
        )

        # From VERIFYING
        self.add_transition(
            ExecutionState.VERIFYING,
            ExecutionState.SUCCESS,
            on_transition=lambda: self._log("Verification passed"),
        )
        self.add_transition(
            ExecutionState.VERIFYING,
            ExecutionState.FAILED,
            on_transition=lambda: self._log("Verification failed"),
        )

        # From FAILED, CANCELLED, SUCCESS - can retry
        self.add_transition(
            ExecutionState.FAILED,
            ExecutionState.PLANNING,
            on_transition=lambda: self._log("Retrying from planning"),
        )
        self.add_transition(
            ExecutionState.CANCELLED,
            ExecutionState.PLANNING,
            on_transition=lambda: self._log("Resuming from cancelled"),
        )

    def add_transition(
        self,
        from_state: ExecutionState,
        to_state: ExecutionState,
        condition: Callable = None,
        on_transition: Callable = None,
    ):
        """Add a valid state transition."""
        if from_state not in self.transitions:
            self.transitions[from_state] = []

        transition = StateTransition(from_state, to_state, condition, on_transition)
        self.transitions[from_state].append(transition)

    def can_transition_to(self, target_state: ExecutionState) -> bool:
        """Check if transition to target state is valid."""
        if self.current_state not in self.transitions:
            return False

        for transition in self.transitions[self.current_state]:
            if transition.to_state == target_state and transition.is_valid():
                return True

        return False

    def transition_to(self, target_state: ExecutionState) -> bool:
        """
        Attempt to transition to target state.

        Returns:
            bool: True if transition successful
        """
        if not self.can_transition_to(target_state):
            self._log(
                f"Invalid transition: {self.current_state.value} -> {target_state.value}",
                level="ERROR",
            )
            return False

        # Find and execute transition
        for transition in self.transitions[self.current_state]:
            if transition.to_state == target_state:
                transition.execute()
                self.current_state = target_state
                self.history.append(target_state)
                self._log(
                    f"Transitioned: {self.history[-2].value} -> {target_state.value}"
                )
                return True

        return False

    def set_metadata(self, key: str, value: Any):
        """Set metadata."""
        self.metadata[key] = value
        self._log(f"Set metadata: {key} = {value}")

    def get_metadata(self, key: str, default=None) -> Any:
        """Get metadata."""
        return self.metadata.get(key, default)

    def _log(self, message: str, level: str = "INFO"):
        """Log state machine event."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] StateMachine: {message}")

    def is_in_terminal_state(self) -> bool:
        """Check if in terminal state (can't proceed further)."""
        terminal_states = {
            ExecutionState.SUCCESS,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        }
        return self.current_state in terminal_states

    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.current_state == ExecutionState.SUCCESS

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "current_state": self.current_state.value,
            "history": [s.value for s in self.history],
            "metadata": self.metadata,
            "is_terminal": self.is_in_terminal_state(),
            "is_success": self.is_success(),
        }

    def __repr__(self):
        return f"StateMachine(current={self.current_state.value}, history={len(self.history)} states)"


class TaskExecutionTracker:
    """Tracks execution of a specific task."""

    def __init__(self, task_id: str, task_name: str):
        self.task_id = task_id
        self.task_name = task_name
        self.state_machine = StateMachine()
        self.attempts = 0
        self.max_retries = 3
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None

    def start(self):
        """Start task execution."""
        self.start_time = datetime.now()
        self.attempts += 1
        self.state_machine.transition_to(ExecutionState.PLANNING)
        print(
            f"Task {self.task_id} started (attempt {self.attempts}/{self.max_retries + 1})"
        )

    def mark_executing(self):
        """Mark task as executing."""
        self.state_machine.transition_to(ExecutionState.READY)
        self.state_machine.transition_to(ExecutionState.EXECUTING)

    def mark_verifying(self):
        """Mark task as verifying."""
        self.state_machine.transition_to(ExecutionState.VERIFYING)

    def mark_success(self, result=None):
        """Mark task as successful."""
        self.result = result
        self.end_time = datetime.now()
        # Don't transition state machine here - let the main agent manage state transitions
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"✓ Task {self.task_id} completed successfully ({duration:.2f}s)")

    def mark_failed(self, error: str):
        """Mark task as failed."""
        self.error = error
        self.end_time = datetime.now()
        # Don't transition state machine here - let the main agent manage state transitions
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"✗ Task {self.task_id} failed ({duration:.2f}s): {error}")

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.attempts <= self.max_retries

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "duration_seconds": duration,
            "result": self.result,
            "error": self.error,
            "state_machine": self.state_machine.to_dict(),
        }

    def __repr__(self):
        return f"TaskTracker({self.task_id}, state={self.state_machine.current_state.value})"
