from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from pathlib import Path
from loguru import logger
from datetime import datetime
import traceback

from app.models.database import Task, Project, TaskEvent, TaskStatus
from app.agents.git_agent import GitAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.developer_agent import DeveloperAgent
from app.agents.tester_agent import TesterAgent
from app.agents.validator_agent import ValidatorAgent
from app.memory.project_memory import ProjectMemory
from app.config import settings


class TaskService:
    """Service for orchestrating task execution"""

    def __init__(self, db: Session):
        self.db = db
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
        )

        # Initialize agents
        self.git_agent = GitAgent()
        self.planner_agent = PlannerAgent(self.llm)
        self.developer_agent = DeveloperAgent(self.llm)
        self.tester_agent = TesterAgent(self.llm)
        self.validator_agent = ValidatorAgent(self.llm)

    async def execute_task(self, task_id: str):
        """Execute complete task workflow"""
        try:
            logger.info(f"[{task_id}] Starting task execution")

            # Load task and project
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found")
                return

            project = (
                self.db.query(Project).filter(Project.id == task.project_id).first()
            )
            if not project:
                logger.error(f"Project {task.project_id} not found")
                self._update_task_status(task, TaskStatus.FAILED, "Project not found")
                return

            repository_path = Path(project.local_path)

            # Step 1: Git Sync
            await self._git_sync_step(task, project, repository_path)
            if task.status == TaskStatus.FAILED:
                return

            # Step 2: Create Branch
            await self._create_branch_step(task, repository_path)
            if task.status == TaskStatus.FAILED:
                return

            # Step 3: Generate Plan
            await self._planning_step(task, project, repository_path)
            if task.status == TaskStatus.FAILED:
                return

            # Step 4: Wait for approval (status set to AWAITING_APPROVAL)
            logger.info(f"[{task_id}] Waiting for human approval")

        except Exception as e:
            logger.error(f"[{task_id}] Task execution failed: {e}")
            logger.error(traceback.format_exc())
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if task:
                self._update_task_status(task, TaskStatus.FAILED, str(e))

    async def continue_after_approval(self, task_id: str):
        """Continue task execution after approval"""
        try:
            logger.info(f"[{task_id}] Continuing after approval")

            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return

            project = (
                self.db.query(Project).filter(Project.id == task.project_id).first()
            )
            repository_path = Path(project.local_path)

            # Step 5: Development
            await self._development_step(task, project, repository_path)
            if task.status == TaskStatus.FAILED:
                return

            # Step 6: Testing
            test_passed = await self._testing_step(task, project, repository_path)
            if task.status == TaskStatus.FAILED:
                return

            # Retry development if tests failed (max 2 retries)
            retry_count = 0
            while not test_passed and retry_count < 2:
                retry_count += 1
                logger.info(
                    f"[{task_id}] Retrying development (attempt {retry_count + 1})"
                )

                await self._development_step(task, project, repository_path)
                if task.status == TaskStatus.FAILED:
                    return

                test_passed = await self._testing_step(task, project, repository_path)
                if task.status == TaskStatus.FAILED:
                    return

            # Step 7: Commit and Push
            await self._commit_push_step(task, repository_path)
            if task.status == TaskStatus.FAILED:
                return

            # Step 8: Generate Report
            await self._report_step(task, project)

            # Mark as completed
            self._update_task_status(
                task, TaskStatus.COMPLETED, completed_at=datetime.utcnow()
            )

            logger.info(f"[{task_id}] Task completed successfully!")

        except Exception as e:
            logger.error(f"[{task_id}] Post-approval execution failed: {e}")
            logger.error(traceback.format_exc())
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if task:
                self._update_task_status(task, TaskStatus.FAILED, str(e))

    async def replan_task(self, task_id: str, feedback: str):
        """Regenerate plan based on feedback"""
        try:
            logger.info(f"[{task_id}] Replanning with feedback")

            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return

            project = (
                self.db.query(Project).filter(Project.id == task.project_id).first()
            )
            repository_path = Path(project.local_path)

            # Regenerate plan with feedback
            await self._planning_step(task, project, repository_path, feedback=feedback)

        except Exception as e:
            logger.error(f"[{task_id}] Replanning failed: {e}")
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if task:
                self._update_task_status(task, TaskStatus.FAILED, str(e))

    async def _git_sync_step(self, task: Task, project: Project, repository_path: Path):
        """Git sync step"""
        try:
            self._update_task_status(
                task, TaskStatus.GIT_SYNC, "Syncing with main branch"
            )
            logger.info(f"[{task.id}] Git sync started")

            # Pull latest changes
            await self.git_agent.pull_latest(repository_path, project.main_branch)

            self._log_event(task, "git_sync_completed", {"branch": project.main_branch})
            logger.info(f"[{task.id}] Git sync completed")

        except Exception as e:
            logger.error(f"[{task.id}] Git sync failed: {e}")
            self._update_task_status(
                task, TaskStatus.FAILED, f"Git sync failed: {str(e)}"
            )

    async def _create_branch_step(self, task: Task, repository_path: Path):
        """Create feature branch step"""
        try:
            logger.info(f"[{task.id}] Creating feature branch")

            # Generate branch name
            branch_name = await self.git_agent.generate_branch_name(task.description)
            task.branch_name = branch_name
            self.db.commit()

            # Create branch
            await self.git_agent.create_branch(repository_path, branch_name)

            self._log_event(task, "branch_created", {"branch_name": branch_name})
            logger.info(f"[{task.id}] Branch created: {branch_name}")

        except Exception as e:
            logger.error(f"[{task.id}] Branch creation failed: {e}")
            self._update_task_status(
                task, TaskStatus.FAILED, f"Branch creation failed: {str(e)}"
            )

    async def _planning_step(
        self, task: Task, project: Project, repository_path: Path, feedback: str = None
    ):
        """Planning step with validation"""
        try:
            self._update_task_status(
                task, TaskStatus.PLANNING, "Generating implementation plan"
            )
            logger.info(f"[{task.id}] Planning started")

            # Load project context
            project_memory = ProjectMemory(str(project.id))
            project_context = await project_memory.get_context()

            # Analyze codebase structure for validation
            codebase_info = await self.planner_agent._analyze_codebase(repository_path)

            # Generate plan
            plan = await self.planner_agent.create_plan(
                task_description=task.description,
                project_context=project_context,
                repository_path=repository_path,
                feedback=feedback,
            )

            # Validate plan against requirements
            validation = await self.validator_agent.validate_plan(
                plan=plan,
                task_description=task.description,
                codebase_info=codebase_info,
            )

            # Log validation results
            logger.info(
                f"[{task.id}] Plan validation: valid={validation.get('is_valid')}, "
                f"score={validation.get('coverage_score')}"
            )

            # Add validation warnings to plan if any critical issues
            critical_issues = [
                issue for issue in validation.get("issues", [])
                if issue.get("severity") == "critical"
            ]

            if critical_issues:
                logger.warning(
                    f"[{task.id}] Plan has {len(critical_issues)} critical issues"
                )
                # Could optionally re-generate plan here

            # Save plan
            plan_path = await self.planner_agent.save_plan(
                plan=plan, task_id=str(task.id), plans_dir=settings.PLANS_PATH
            )

            task.plan_path = plan_path
            self.db.commit()

            # Update status to awaiting approval
            self._update_task_status(
                task, TaskStatus.AWAITING_APPROVAL, "Plan ready for review"
            )
            self._log_event(
                task,
                "plan_generated",
                {
                    "plan_path": plan_path,
                    "validation_score": validation.get("coverage_score", 0),
                    "validation_issues": len(validation.get("issues", [])),
                },
            )

            logger.info(f"[{task.id}] Plan generated and saved: {plan_path}")

        except Exception as e:
            logger.error(f"[{task.id}] Planning failed: {e}")
            self._update_task_status(
                task, TaskStatus.FAILED, f"Planning failed: {str(e)}"
            )

    async def _development_step(
        self, task: Task, project: Project, repository_path: Path
    ):
        """Development step with validation"""
        try:
            self._update_task_status(
                task, TaskStatus.IN_PROGRESS, "Implementing feature"
            )
            logger.info(f"[{task.id}] Development started")

            # Load plan
            plan = Path(task.plan_path).read_text(encoding="utf-8")

            # Load project context
            project_memory = ProjectMemory(str(project.id))
            project_context = await project_memory.get_context()

            # Implement
            result = await self.developer_agent.implement(
                plan=plan,
                project_context=project_context,
                repository_path=repository_path,
            )

            # Store files info in task metadata for later use
            task.files_created = result["files_created"]
            task.files_modified = result["files_modified"]
            task.implementation_summary = result["summary"]
            self.db.commit()

            # Validate implementation
            validation = await self.validator_agent.validate_implementation(
                plan=plan,
                task_description=task.description,
                files_created=result["files_created"],
                files_modified=result["files_modified"],
                repository_path=repository_path,
            )

            logger.info(
                f"[{task.id}] Implementation validation: valid={validation.get('is_valid')}, "
                f"score={validation.get('adherence_score')}"
            )

            self._log_event(
                task,
                "development_completed",
                {
                    "files_created": len(result["files_created"]),
                    "files_modified": len(result["files_modified"]),
                    "validation_score": validation.get("adherence_score", 0),
                },
            )

            logger.info(f"[{task.id}] Development completed: {result['summary']}")

        except Exception as e:
            logger.error(f"[{task.id}] Development failed: {e}")
            self._update_task_status(
                task, TaskStatus.FAILED, f"Development failed: {str(e)}"
            )

    async def _testing_step(
        self, task: Task, project: Project, repository_path: Path
    ) -> bool:
        """Testing step - returns True if tests passed"""
        try:
            self._update_task_status(task, TaskStatus.TESTING, "Running tests")
            logger.info(f"[{task.id}] Testing started")

            # Get files that were created/modified
            files_created = getattr(task, "files_created", []) or []
            files_modified = getattr(task, "files_modified", []) or []

            # Run tests
            test_results = await self.tester_agent.run_tests(
                repository_path=repository_path,
                files_modified=files_modified,
                files_created=files_created,
            )

            passed = test_results.get("all_passed", False)

            # Store test results in task for report generation
            task.test_results = test_results
            self.db.commit()

            self._log_event(
                task,
                "testing_completed",
                {
                    "passed": test_results.get("passed", 0),
                    "failed": test_results.get("failed", 0),
                    "all_passed": passed,
                },
            )

            logger.info(
                f"[{task.id}] Testing completed: {'passed' if passed else 'failed'} "
                f"({test_results.get('passed', 0)}/{test_results.get('total', 0)} tests)"
            )

            return passed

        except Exception as e:
            logger.error(f"[{task.id}] Testing failed: {e}")
            self._update_task_status(
                task, TaskStatus.FAILED, f"Testing failed: {str(e)}"
            )
            return False

    async def _commit_push_step(self, task: Task, repository_path: Path):
        """Commit and push step"""
        try:
            logger.info(f"[{task.id}] Committing and pushing changes")

            # Generate commit message
            commit_message = await self.git_agent.generate_commit_message(
                task_description=task.description, files_modified=[], files_created=[]
            )

            # Commit and push
            commit_hash = await self.git_agent.commit_and_push(
                repo_path=repository_path,
                branch_name=task.branch_name,
                commit_message=commit_message,
            )

            task.commit_hash = commit_hash
            self.db.commit()

            self._log_event(
                task,
                "code_pushed",
                {"branch": task.branch_name, "commit_hash": commit_hash},
            )

            logger.info(f"[{task.id}] Changes pushed: {commit_hash}")

        except Exception as e:
            logger.error(f"[{task.id}] Commit/push failed: {e}")
            self._update_task_status(
                task, TaskStatus.FAILED, f"Commit/push failed: {str(e)}"
            )

    async def _report_step(self, task: Task, project: Project):
        """Generate completion report with actual test results"""
        try:
            logger.info(f"[{task.id}] Generating completion report")

            # Load plan
            plan = Path(task.plan_path).read_text(encoding="utf-8")

            # Get actual test results from task
            test_results = getattr(task, "test_results", None) or {
                "passed": 0,
                "failed": 0,
                "total": 0,
                "output": "No test results available",
                "all_passed": False,
            }

            # Get implementation summary
            implementation_summary = getattr(
                task, "implementation_summary", "Implementation completed"
            )

            # Generate report with real data
            report = await self.planner_agent.generate_report(
                task_description=task.description,
                plan=plan,
                implementation_summary=implementation_summary,
                test_results=test_results,
                commit_hash=task.commit_hash or "No commit",
                branch_name=task.branch_name or "No branch",
            )

            # Save report
            report_path = await self.planner_agent.save_report(
                report=report, task_id=str(task.id), reports_dir=settings.REPORTS_PATH
            )

            task.report_path = report_path
            self.db.commit()

            self._log_event(task, "report_generated", {"report_path": report_path})

            logger.info(f"[{task.id}] Report generated: {report_path}")

        except Exception as e:
            logger.error(f"[{task.id}] Report generation failed: {e}")
            logger.error(traceback.format_exc())
            # Don't fail the task for report generation issues

    def _update_task_status(
        self, task: Task, status: TaskStatus, message: str = None, **kwargs
    ):
        """Update task status"""
        task.status = status
        if message:
            if status == TaskStatus.FAILED:
                task.error_message = message

        for key, value in kwargs.items():
            setattr(task, key, value)

        self.db.commit()

        if message:
            self._log_event(
                task, "status_changed", {"status": status.value, "message": message}
            )

    def _log_event(self, task: Task, event_type: str, data: dict):
        """Log task event"""
        try:
            event = TaskEvent(task_id=task.id, event_type=event_type, data=data)
            self.db.add(event)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
