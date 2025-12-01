"""
Task decomposer - breaks complex goals into subtasks.
Distinguishes between tasks that need AI vs tasks that use shortcuts.
"""

from enum import Enum
from typing import List, Dict, Any
import json


class TaskType(Enum):
    """Types of tasks."""

    SHORTCUT = "shortcut"  # Use keyboard shortcuts - deterministic
    AI = "ai"  # Use AI for complex decisions
    VERIFY = "verify"  # Verify something happened
    COMMAND = "command"  # Run terminal command


class Task:
    """Represents a single task."""

    def __init__(
        self,
        id: str,
        title: str,
        type: TaskType,
        description: str = "",
        params: Dict[str, Any] = None,
        depends_on: List[str] = None,
        success_criteria: Dict[str, Any] = None,
    ):
        self.id = id
        self.title = title
        self.type = type
        self.description = description
        self.params = params or {}
        self.depends_on = depends_on or []
        self.success_criteria = success_criteria or {}
        self.status = "pending"  # pending, running, completed, failed
        self.result = None

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "description": self.description,
            "params": self.params,
            "depends_on": self.depends_on,
            "success_criteria": self.success_criteria,
            "status": self.status,
            "result": self.result,
        }

    def __repr__(self):
        return f"Task({self.id}: {self.title}, type={self.type.value}, status={self.status})"


class TaskPlan:
    """Represents a plan of tasks to accomplish a goal."""

    def __init__(self, goal: str):
        self.goal = goal
        self.tasks: List[Task] = []
        self.execution_order = []

    def add_task(self, task: Task):
        """Add a task to the plan."""
        self.tasks.append(task)

    def add_shortcut_task(
        self,
        id: str,
        title: str,
        action: str,
        params: Dict = None,
        depends_on: List[str] = None,
        success_criteria: Dict = None,
    ):
        """Add a shortcut-based task."""
        task = Task(
            id=id,
            title=title,
            type=TaskType.SHORTCUT,
            description=f"Execute shortcut action: {action}",
            params={"action": action, **(params or {})},
            depends_on=depends_on,
            success_criteria=success_criteria,
        )
        self.add_task(task)

    def add_ai_task(
        self,
        id: str,
        title: str,
        objective: str,
        depends_on: List[str] = None,
        success_criteria: Dict = None,
    ):
        """Add an AI-based task."""
        task = Task(
            id=id,
            title=title,
            type=TaskType.AI,
            description=objective,
            params={"objective": objective},
            depends_on=depends_on,
            success_criteria=success_criteria,
        )
        self.add_task(task)

    def add_verification_task(
        self,
        id: str,
        title: str,
        verification_type: str,
        params: Dict = None,
        depends_on: List[str] = None,
    ):
        """Add a verification task."""
        task = Task(
            id=id,
            title=title,
            type=TaskType.VERIFY,
            description=f"Verify: {verification_type}",
            params={"verification_type": verification_type, **(params or {})},
            depends_on=depends_on,
        )
        self.add_task(task)

    def add_command_task(
        self,
        id: str,
        title: str,
        command: str,
        depends_on: List[str] = None,
        success_criteria: Dict = None,
    ):
        """Add a command execution task."""
        task = Task(
            id=id,
            title=title,
            type=TaskType.COMMAND,
            description=f"Execute: {command}",
            params={"command": command},
            depends_on=depends_on,
            success_criteria=success_criteria,
        )
        self.add_task(task)

    def get_next_executable_task(self):
        """Get the next task that can be executed (dependencies met)."""
        for task in self.tasks:
            if task.status == "pending":
                # Check if all dependencies are completed
                deps_met = all(
                    self.get_task_by_id(dep_id).status == "completed"
                    for dep_id in task.depends_on
                )
                if deps_met:
                    return task
        return None

    def get_task_by_id(self, task_id: str) -> Task:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def to_dict(self):
        return {
            "goal": self.goal,
            "tasks": [task.to_dict() for task in self.tasks],
            "execution_order": self.execution_order,
        }

    def __repr__(self):
        return f"TaskPlan(goal='{self.goal}', {len(self.tasks)} tasks)"


class TaskDecomposer:
    """Decomposes complex goals into executable subtasks."""

    def decompose(self, goal: str) -> TaskPlan:
        """
        Decomposes a goal into subtasks.

        Args:
            goal: The high-level goal

        Returns:
            TaskPlan: Structured plan of tasks
        """
        goal_lower = goal.lower()
        plan = TaskPlan(goal)

        # Example decompositions

        # GOAL: Open VSCode and create a new Python file
        if "open" in goal_lower and "vscode" in goal_lower:
            plan.add_shortcut_task(
                id="open_vscode",
                title="Open VSCode",
                action="open_application",
                params={"app_name": "vscode"},
                success_criteria={"app_running": "vscode"},
            )
            plan.add_verification_task(
                id="verify_vscode_open",
                title="Verify VSCode opened",
                verification_type="app_running",
                params={"app_name": "vscode"},
                depends_on=["open_vscode"],
            )
            return plan

        # GOAL: Create a new file with specific content
        if "create" in goal_lower and "file" in goal_lower:
            plan.add_shortcut_task(
                id="create_new_file",
                title="Create new file",
                action="open_new_tab",
                success_criteria={"new_window": True},
            )
            plan.add_verification_task(
                id="verify_file_created",
                title="Verify new file",
                verification_type="window_ready",
                depends_on=["create_new_file"],
            )
            plan.add_ai_task(
                id="write_content",
                title="Write file content",
                objective="Write the required content to the new file",
                depends_on=["verify_file_created"],
                success_criteria={"content_written": True},
            )
            return plan

        # GOAL: Install a Python package
        if "install" in goal_lower and ("package" in goal_lower or "pip" in goal_lower):
            package = self._extract_package_name(goal)
            plan.add_shortcut_task(
                id="open_terminal",
                title="Open terminal",
                action="open_application",
                params={"app_name": "cmd"},
                success_criteria={"app_running": "cmd"},
            )
            plan.add_command_task(
                id="install_package",
                title=f"Install {package}",
                command=f"pip install {package}",
                depends_on=["open_terminal"],
                success_criteria={"package_installed": True},
            )
            plan.add_verification_task(
                id="verify_install",
                title=f"Verify {package} installed",
                verification_type="package_installed",
                params={"package_name": package},
                depends_on=["install_package"],
            )
            return plan

        # GOAL: Open an application
        if "open" in goal_lower and any(
            app in goal_lower for app in ["notepad", "chrome", "firefox", "explorer"]
        ):
            app_name = self._extract_app_name(goal)
            plan.add_shortcut_task(
                id="open_app",
                title=f"Open {app_name}",
                action="open_application",
                params={"app_name": app_name},
                success_criteria={"app_running": app_name},
            )
            plan.add_verification_task(
                id="verify_app_open",
                title=f"Verify {app_name} opened",
                verification_type="app_running",
                params={"app_name": app_name},
                depends_on=["open_app"],
            )
            return plan

        # GOAL: Write code / complex task
        if any(
            keyword in goal_lower
            for keyword in ["write", "code", "function", "debug", "fix", "implement"]
        ):
            plan.add_ai_task(
                id="analyze_task",
                title="Analyze task requirements",
                objective=goal,
                success_criteria={"analysis_complete": True},
            )
            plan.add_ai_task(
                id="execute_ai_task",
                title="Execute AI task",
                objective=goal,
                depends_on=["analyze_task"],
                success_criteria={"task_complete": True},
            )
            return plan

        # Default: treat as AI task
        plan.add_ai_task(
            id="execute_goal",
            title="Execute goal",
            objective=goal,
            success_criteria={"goal_complete": True},
        )
        return plan

    def _extract_package_name(self, goal: str) -> str:
        """Extract package name from goal."""
        words = goal.lower().split()
        
        # Skip common articles and prepositions
        skip_words = {'the', 'a', 'an', 'using', 'with', 'via', 'package'}
        
        for i, word in enumerate(words):
            if word in ['install']:
                # Look for the next non-skip word
                for j in range(i + 1, len(words)):
                    if words[j] not in skip_words:
                        return words[j]
        
        # Fallback: look for common package names
        common_packages = ['requests', 'flask', 'django', 'numpy', 'pandas', 'matplotlib']
        for pkg in common_packages:
            if pkg in goal.lower():
                return pkg
        
        return "unknown"

    def _extract_app_name(self, goal: str) -> str:
        """Extract application name from goal."""
        apps = {
            "notepad": "notepad",
            "vscode": "vscode",
            "code": "vscode",
            "chrome": "chrome",
            "firefox": "firefox",
            "explorer": "explorer",
            "cmd": "cmd",
            "powershell": "powershell",
        }
        goal_lower = goal.lower()
        for keyword, app_name in apps.items():
            if keyword in goal_lower:
                return app_name
        return "unknown"


# Global decomposer instance
decomposer = TaskDecomposer()
