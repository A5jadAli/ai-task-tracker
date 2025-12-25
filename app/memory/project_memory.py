from pathlib import Path
from typing import Dict, Optional
import json
from loguru import logger
from app.config import settings


class ProjectMemory:
    """Manages project-specific context and memory"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.memory_file = settings.MEMORY_PATH / f"project_{project_id}.json"
        self._memory_cache = None

    async def get_context(self) -> Dict:
        """Get project context from memory"""
        try:
            if self._memory_cache is not None:
                return self._memory_cache

            if self.memory_file.exists():
                logger.info(f"Loading project context for {self.project_id}")
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self._memory_cache = json.load(f)
                return self._memory_cache
            else:
                logger.info(
                    f"No existing context for project {self.project_id}, using defaults"
                )
                return self._get_default_context()

        except Exception as e:
            logger.error(f"Failed to load project context: {e}")
            return self._get_default_context()

    async def save_context(self, context: Dict) -> None:
        """Save project context to memory"""
        try:
            logger.info(f"Saving project context for {self.project_id}")

            # Ensure directory exists
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(context, f, indent=2)

            # Update cache
            self._memory_cache = context

            logger.info(f"Project context saved successfully")

        except Exception as e:
            logger.error(f"Failed to save project context: {e}")
            raise

    async def update_context(self, updates: Dict) -> None:
        """Update specific fields in project context"""
        try:
            context = await self.get_context()
            context.update(updates)
            await self.save_context(context)

        except Exception as e:
            logger.error(f"Failed to update project context: {e}")
            raise

    async def add_learning(self, learning: Dict) -> None:
        """Add a learning/pattern from completed tasks"""
        try:
            context = await self.get_context()

            if "learnings" not in context:
                context["learnings"] = []

            # Add new learning
            context["learnings"].append(learning)

            # Keep only last 50 learnings
            if len(context["learnings"]) > 50:
                context["learnings"] = context["learnings"][-50:]

            await self.save_context(context)
            logger.info(f"Added learning to project memory")

        except Exception as e:
            logger.error(f"Failed to add learning: {e}")

    async def get_relevant_learnings(self, task_description: str) -> list:
        """Get learnings relevant to current task"""
        try:
            context = await self.get_context()
            learnings = context.get("learnings", [])

            # Simple relevance: return recent learnings
            # TODO: Implement semantic search with embeddings
            return learnings[-10:]  # Last 10 learnings

        except Exception as e:
            logger.error(f"Failed to get relevant learnings: {e}")
            return []

    def _get_default_context(self) -> Dict:
        """Get default project context"""
        return {
            "tech_stack": ["Python"],
            "coding_style": "PEP 8",
            "test_framework": "pytest",
            "conventions": {
                "docstring_style": "Google",
                "max_line_length": 100,
                "use_type_hints": True,
            },
            "learnings": [],
            "common_patterns": [],
            "dependencies": [],
        }

    async def extract_context_from_project(self, repository_path: Path) -> Dict:
        """Extract context by analyzing the project structure"""
        try:
            logger.info(f"Extracting context from project at {repository_path}")

            context = self._get_default_context()

            # Detect tech stack from files
            tech_stack = set()

            # Check for Python
            if list(repository_path.glob("**/*.py")):
                tech_stack.add("Python")

            # Check for requirements.txt or setup.py
            if (repository_path / "requirements.txt").exists():
                requirements = (repository_path / "requirements.txt").read_text()
                if "fastapi" in requirements.lower():
                    tech_stack.add("FastAPI")
                if "django" in requirements.lower():
                    tech_stack.add("Django")
                if "flask" in requirements.lower():
                    tech_stack.add("Flask")
                if "sqlalchemy" in requirements.lower():
                    tech_stack.add("SQLAlchemy")
                if "pytest" in requirements.lower():
                    context["test_framework"] = "pytest"

            # Check for package.json (JavaScript/Node.js)
            if (repository_path / "package.json").exists():
                tech_stack.add("Node.js")
                try:
                    package_json = json.loads(
                        (repository_path / "package.json").read_text()
                    )
                    dependencies = package_json.get("dependencies", {})
                    if "react" in dependencies:
                        tech_stack.add("React")
                    if "vue" in dependencies:
                        tech_stack.add("Vue")
                    if "express" in dependencies:
                        tech_stack.add("Express")
                except:
                    pass

            # Check for Docker
            if (repository_path / "Dockerfile").exists():
                tech_stack.add("Docker")

            context["tech_stack"] = list(tech_stack) if tech_stack else ["Python"]

            # Detect coding style
            if (repository_path / ".flake8").exists() or (
                repository_path / "setup.cfg"
            ).exists():
                context["coding_style"] = "PEP 8 (enforced)"

            if (repository_path / ".black").exists() or (
                repository_path / "pyproject.toml"
            ).exists():
                try:
                    pyproject = (repository_path / "pyproject.toml").read_text()
                    if "black" in pyproject:
                        context["coding_style"] = "Black"
                except:
                    pass

            logger.info(f"Extracted context: {context['tech_stack']}")

            return context

        except Exception as e:
            logger.error(f"Failed to extract context: {e}")
            return self._get_default_context()
