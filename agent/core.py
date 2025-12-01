# -*- coding: utf-8 -*-
import time
import os
from typing import Dict, Any
from .shortcuts_actions import ShortcutsActionExecutor
from .verification import Verifier
from .task_decomposer import decomposer, TaskType
from .brain import AgentBrain
from .state_machine import StateMachine, ExecutionState, TaskExecutionTracker
from dotenv import load_dotenv

load_dotenv()


class AutonomousAgent:
    """
    New architecture: Hybrid agent that uses shortcuts for deterministic tasks
    and AI for complex decision-making tasks.
    """

    def __init__(self):
        self.shortcuts = ShortcutsActionExecutor()
        self.verifier = Verifier()
        self.brain = AgentBrain()
        self.state_machine = StateMachine()
        self.history = []
        self.human_in_loop = os.getenv("HUMAN_IN_THE_LOOP", "false").lower() == "true"
        self.current_task_tracker = None

    def run(self, goal: str):
        """
        Run agent with a goal using hybrid architecture.

        Args:
            goal: The goal to accomplish
        """
        print(f"\n{'='*60}")
        print(f"[GOAL] {goal}")
        print(f"{'='*60}\n")

        # Phase 1: Initialize
        self.state_machine.transition_to(ExecutionState.PLANNING)

        # Phase 2: Decompose goal into tasks
        print("[*] Decomposing goal into tasks...\n")
        task_plan = decomposer.decompose(goal)
        self.state_machine.set_metadata("task_plan", task_plan)

        print(f"Task Plan: {len(task_plan.tasks)} tasks identified\n")
        for task in task_plan.tasks:
            print(f"  {task.id}: [{task.type.value}] {task.title}")
            if task.depends_on:
                print(f"     Depends on: {task.depends_on}")
        print()

        # Phase 3: Ready to execute
        if not self.state_machine.transition_to(ExecutionState.READY):
            print("✗ Failed to transition to READY state")
            return False

        # Phase 4: Execute tasks
        if not self.state_machine.transition_to(ExecutionState.EXECUTING):
            print("✗ Failed to transition to EXECUTING state")
            return False

        try:
            while True:
                # Get next executable task
                next_task = task_plan.get_next_executable_task()

                if not next_task:
                    # Check if all tasks succeeded or if any failed
                    failed_tasks = [t for t in task_plan.tasks if t.status == "failed"]

                    if failed_tasks:
                        # Some tasks failed
                        print("\n[FAIL] Some tasks failed:")
                        for task in failed_tasks:
                            print(f"  [-] {task.id}: {task.title}")
                        self.state_machine.transition_to(ExecutionState.FAILED)
                        return False

                    # All tasks completed successfully
                    print("\n[OK] All tasks completed successfully!")
                    self.state_machine.transition_to(ExecutionState.VERIFYING)
                    self.state_machine.transition_to(ExecutionState.SUCCESS)
                    return True

                print(f"\n{'─'*60}")
                print(f"[>] Executing: [{next_task.type.value}] {next_task.title}")
                print(f"{'─'*60}")

                # Create tracker for this task
                tracker = TaskExecutionTracker(next_task.id, next_task.title)
                tracker.start()
                self.current_task_tracker = tracker

                # Execute task based on type
                success = False

                if next_task.type == TaskType.SHORTCUT:
                    success = self._execute_shortcut_task(next_task)

                elif next_task.type == TaskType.COMMAND:
                    success = self._execute_command_task(next_task)

                elif next_task.type == TaskType.VERIFY:
                    success = self._execute_verification_task(next_task)

                elif next_task.type == TaskType.AI:
                    success = self._execute_ai_task(next_task, goal)

                # Update task status
                if success:
                    next_task.status = "completed"
                    tracker.mark_success()
                else:
                    next_task.status = "failed"
                    tracker.mark_failed("Task execution failed")
                    print(f"\n[FAIL] Task {next_task.id} failed")

                    if not tracker.can_retry():
                        print(f"[FAIL] Max retries exceeded for {next_task.id}")
                        self.state_machine.transition_to(ExecutionState.FAILED)
                        return False

                self.history.append(tracker.to_dict())

        except KeyboardInterrupt:
            print("\n\n[WARN] Agent interrupted by user")
            self.state_machine.transition_to(ExecutionState.CANCELLED)
            return False
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            self.state_machine.transition_to(ExecutionState.FAILED)
            return False

    def _execute_shortcut_task(self, task) -> bool:
        """Execute a shortcut-based task."""
        try:
            action = task.params.get("action")

            if action == "open_application":
                app_name = task.params.get("app_name")
                result = self.shortcuts.open_application(app_name)

                # Verify
                if result and task.success_criteria.get("app_running"):
                    time.sleep(1)
                    verified = self.verifier.app_is_running(app_name, timeout=5)
                    return verified
                return result

            elif action == "open_new_tab":
                result = self.shortcuts.open_new_tab()
                return result

            elif action == "close_tab":
                result = self.shortcuts.close_tab()
                return result

            elif action == "switch_tab":
                direction = task.params.get("direction", "next")
                result = self.shortcuts.switch_tab(direction)
                return result

            elif action == "save_file":
                result = self.shortcuts.save_file()
                return result

            elif action == "close_application":
                app_name = task.params.get("app_name")
                result = self.shortcuts.close_application(app_name)
                return result

            else:
                print(f"✗ Unknown shortcut action: {action}")
                return False

        except Exception as e:
            print(f"✗ Error executing shortcut: {e}")
            return False

    def _execute_command_task(self, task) -> bool:
        """Execute a terminal command task."""
        try:
            command = task.params.get("command")
            timeout = task.params.get("timeout", 30)

            print(f"Executing command: {command}")

            # Run command and verify it succeeds
            success = self.verifier.command_succeeds(command, timeout=timeout)

            if success and task.success_criteria.get("package_installed"):
                package = task.params.get("package_name")
                if package:
                    time.sleep(1)
                    verified = self.verifier.package_is_installed(package)
                    return verified

            return success

        except Exception as e:
            print(f"✗ Error executing command: {e}")
            return False

    def _execute_verification_task(self, task) -> bool:
        """Execute a verification task."""
        try:
            verification_type = task.params.get("verification_type")

            if verification_type == "app_running":
                app_name = task.params.get("app_name")
                return self.verifier.app_is_running(app_name)

            elif verification_type == "file_exists":
                file_path = task.params.get("file_path")
                return self.verifier.file_exists(file_path)

            elif verification_type == "file_contains":
                file_path = task.params.get("file_path")
                text = task.params.get("text")
                return self.verifier.file_contains_text(file_path, text)

            elif verification_type == "package_installed":
                package = task.params.get("package_name")
                return self.verifier.package_is_installed(package)

            else:
                print(f"Unknown verification type: {verification_type}")
                return False

        except Exception as e:
            print(f"✗ Error verifying: {e}")
            return False

    def _execute_ai_task(self, task, goal: str) -> bool:
        """Execute an AI-based task."""
        try:
            objective = task.params.get("objective")

            print(f"Using AI to accomplish: {objective}")

            # Ask AI for advice/execution
            decision = self.brain.think_about_task(objective)

            if "error" in decision:
                print(f"✗ AI Error: {decision['error']}")
                return False

            thought = decision.get("thought", "")
            action_type = decision.get("action_type", "advice")
            content = decision.get("content", "")

            print(f"AI Thought: {thought}")

            if action_type == "code":
                print(f"\n📝 AI Generated Code:\n{content}\n")

                if self.human_in_loop:
                    user_input = input("Execute this code? [Y/n]: ")
                    if user_input.lower() == "n":
                        print("Code execution skipped by user")
                        return False

                # For code tasks, we return True if AI provided code
                return True

            elif action_type == "instructions":
                print(f"\n📋 AI Instructions:\n{content}\n")
                return True

            else:
                return True

        except Exception as e:
            print(f"✗ Error executing AI task: {e}")
            return False


class SimpleAgentDemo:
    """Simple demonstration of the hybrid agent on specific tasks."""

    def __init__(self):
        self.agent = AutonomousAgent()

    def demo_open_app(self):
        """Demo: Open an application."""
        self.agent.run("Open VSCode")

    def demo_install_package(self):
        """Demo: Install a Python package."""
        self.agent.run("Install the flask package using pip")

    def demo_create_file(self):
        """Demo: Create a file."""
        self.agent.run("Create a new Python file with a simple hello world function")

    def demo_complex_task(self):
        """Demo: Complex task mixing shortcuts and AI."""
        self.agent.run(
            "Open VSCode and write a Python function that calculates fibonacci"
        )
