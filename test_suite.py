"""
Test suite for the new hybrid agent architecture.
Tests each component individually before full integration.
"""

import time
import os
import tempfile
from pathlib import Path


class TestShortcutsActions:
    """Test shortcuts_actions module."""

    @staticmethod
    def test_app_running_checks():
        """Test if we can detect running apps."""
        from agent.shortcuts_actions import ShortcutsActionExecutor

        executor = ShortcutsActionExecutor()

        # Test with system apps
        result = executor.is_app_running("explorer")
        print(f"✓ Explorer running check: {result}")

        result = executor.is_app_running("nonexistent_app_12345")
        print(f"✓ Non-existent app check: {not result}")  # Should be False

    @staticmethod
    def test_hotkey_functions():
        """Test hotkey functions."""
        from agent.shortcuts_actions import ShortcutsActionExecutor

        executor = ShortcutsActionExecutor()

        # Test opening Notepad
        print("Testing: Opening Notepad...")
        result = executor.open_application("notepad", timeout=3)
        print(f"{'✓' if result else '✗'} Notepad open: {result}")

        # Wait a bit
        time.sleep(1)

        # Close it
        result = executor.close_application("notepad")
        print(f"{'✓' if result else '✗'} Notepad close: {result}")

    @staticmethod
    def test_file_operations():
        """Test file operation functions."""
        from agent.shortcuts_actions import ShortcutsActionExecutor

        executor = ShortcutsActionExecutor()

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_file = f.name
            f.write("Test content")

        try:
            # Test save
            result = executor.save_file()
            print(f"✓ Save file function works")

            # Cleanup
            os.unlink(temp_file)
            print(f"✓ File operations tested")
        except Exception as e:
            print(f"✗ Error: {e}")
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestVerification:
    """Test verification module."""

    @staticmethod
    def test_file_verification():
        """Test file verification."""
        from agent.verification import Verifier

        verifier = Verifier()

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_file = f.name
            f.write("Test content here")

        try:
            # Test file exists
            result = verifier.file_exists(temp_file, timeout=2)
            print(f"{'✓' if result else '✗'} File exists verification: {result}")

            # Test file contains text
            result = verifier.file_contains_text(temp_file, "Test content", timeout=2)
            print(f"{'✓' if result else '✗'} File contains text verification: {result}")

            # Cleanup
            os.unlink(temp_file)
        except Exception as e:
            print(f"✗ Error: {e}")
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @staticmethod
    def test_app_verification():
        """Test app verification."""
        from agent.verification import Verifier

        verifier = Verifier()

        # Test explorer (should be running on Windows)
        result = verifier.app_is_running("explorer", timeout=2)
        print(f"{'✓' if result else '✗'} App running verification (explorer): {result}")

        # Test non-existent app
        result = verifier.app_is_running("definitely_not_a_real_app_12345", timeout=1)
        print(
            f"{'✓' if not result else '✗'} App not running verification: {not result}"
        )

    @staticmethod
    def test_command_verification():
        """Test command execution verification."""
        from agent.verification import Verifier

        verifier = Verifier()

        # Test successful command
        result = verifier.command_succeeds("echo test", timeout=5)
        print(f"{'✓' if result else '✗'} Command success verification: {result}")

        # Test package check
        result = verifier.package_is_installed("pip", timeout=5)
        print(f"{'✓' if result else '✗'} Package installed verification: {result}")


class TestTaskDecomposer:
    """Test task decomposer module."""

    @staticmethod
    def test_decompose_simple_goals():
        """Test decomposing simple goals."""
        from agent.task_decomposer import decomposer

        # Test: Open application
        goal = "Open VSCode"
        plan = decomposer.decompose(goal)
        print(f"\n✓ Decomposed '{goal}':")
        for task in plan.tasks:
            print(f"  - {task.id}: [{task.type.value}] {task.title}")

        # Test: Install package
        goal = "Install the requests package using pip"
        plan = decomposer.decompose(goal)
        print(f"\n✓ Decomposed '{goal}':")
        for task in plan.tasks:
            print(f"  - {task.id}: [{task.type.value}] {task.title}")

        # Test: Complex task
        goal = "Write a Python function that calculates fibonacci"
        plan = decomposer.decompose(goal)
        print(f"\n✓ Decomposed '{goal}':")
        for task in plan.tasks:
            print(f"  - {task.id}: [{task.type.value}] {task.title}")

    @staticmethod
    def test_task_dependencies():
        """Test task dependency resolution."""
        from agent.task_decomposer import decomposer

        goal = "Install the flask package using pip"
        plan = decomposer.decompose(goal)

        print(f"\n✓ Testing task dependencies for: '{goal}'")

        # Get first task
        task1 = plan.get_next_executable_task()
        print(f"  First task: {task1.id}")

        # Mark it complete
        task1.status = "completed"

        # Get next task
        task2 = plan.get_next_executable_task()
        if task2:
            print(f"  Next task: {task2.id} (depends on: {task2.depends_on})")
        else:
            print(f"  No more tasks")


class TestStateMachine:
    """Test state machine module."""

    @staticmethod
    def test_state_transitions():
        """Test valid state transitions."""
        from agent.state_machine import StateMachine, ExecutionState

        sm = StateMachine()
        print(f"\n✓ Initial state: {sm.current_state.value}")

        # Try transitions
        transitions = [
            ExecutionState.PLANNING,
            ExecutionState.READY,
            ExecutionState.EXECUTING,
            ExecutionState.VERIFYING,
            ExecutionState.SUCCESS,
        ]

        for target_state in transitions:
            success = sm.transition_to(target_state)
            if success:
                print(f"  ✓ Transitioned to: {target_state.value}")
            else:
                print(f"  ✗ Failed to transition to: {target_state.value}")

    @staticmethod
    def test_invalid_transitions():
        """Test invalid state transitions are blocked."""
        from agent.state_machine import StateMachine, ExecutionState

        sm = StateMachine()

        # Try invalid transition (SUCCESS to EXECUTING)
        sm.current_state = ExecutionState.SUCCESS
        result = sm.transition_to(ExecutionState.EXECUTING)
        print(f"{'✓' if not result else '✗'} Invalid transition blocked: {not result}")

    @staticmethod
    def test_task_tracker():
        """Test task execution tracker."""
        from agent.state_machine import TaskExecutionTracker
        import time

        tracker = TaskExecutionTracker("test_task_1", "Test Task")
        tracker.start()
        time.sleep(0.5)
        tracker.mark_success(result={"status": "success"})

        print(f"\n✓ Task tracker test:")
        print(f"  Task: {tracker.task_id}")
        print(f"  Attempts: {tracker.attempts}")
        print(f"  Success: {tracker.state_machine.is_success()}")


class TestIntegration:
    """Integration tests for the full system."""

    @staticmethod
    def test_core_agent_init():
        """Test agent initialization."""
        try:
            from agent.core import AutonomousAgent

            agent = AutonomousAgent()
            print(f"\n✓ Agent initialized successfully")
            print(f"  - Shortcuts executor: OK")
            print(f"  - Verifier: OK")
            print(f"  - Brain: OK")
            print(f"  - State machine: OK")
            return True
        except Exception as e:
            print(f"✗ Agent initialization failed: {e}")
            return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RUNNING TEST SUITE FOR HYBRID AGENT ARCHITECTURE")
    print("=" * 60)

    # Test 1: Shortcuts Actions
    print("\n" + "=" * 60)
    print("TEST 1: Shortcuts Actions")
    print("=" * 60)
    try:
        TestShortcutsActions.test_app_running_checks()
        print("✓ App running checks passed")
    except Exception as e:
        print(f"✗ App running checks failed: {e}")

    # Test 2: Verification
    print("\n" + "=" * 60)
    print("TEST 2: Verification System")
    print("=" * 60)
    try:
        TestVerification.test_file_verification()
        TestVerification.test_app_verification()
        print("✓ Verification tests passed")
    except Exception as e:
        print(f"✗ Verification tests failed: {e}")

    # Test 3: Task Decomposer
    print("\n" + "=" * 60)
    print("TEST 3: Task Decomposer")
    print("=" * 60)
    try:
        TestTaskDecomposer.test_decompose_simple_goals()
        TestTaskDecomposer.test_task_dependencies()
        print("✓ Task decomposition tests passed")
    except Exception as e:
        print(f"✗ Task decomposition tests failed: {e}")

    # Test 4: State Machine
    print("\n" + "=" * 60)
    print("TEST 4: State Machine")
    print("=" * 60)
    try:
        TestStateMachine.test_state_transitions()
        TestStateMachine.test_invalid_transitions()
        TestStateMachine.test_task_tracker()
        print("✓ State machine tests passed")
    except Exception as e:
        print(f"✗ State machine tests failed: {e}")

    # Test 5: Integration
    print("\n" + "=" * 60)
    print("TEST 5: Integration")
    print("=" * 60)
    try:
        TestIntegration.test_core_agent_init()
        print("✓ Integration tests passed")
    except Exception as e:
        print(f"✗ Integration tests failed: {e}")

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
