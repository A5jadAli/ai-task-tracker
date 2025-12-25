from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from loguru import logger
import operator

from app.config import settings
from app.agents.planner_agent import PlannerAgent
from app.agents.developer_agent import DeveloperAgent
from app.agents.tester_agent import TesterAgent
from app.agents.git_agent import GitAgent
from app.memory.project_memory import ProjectMemory


class AgentState(TypedDict):
    """State shared between all agents"""

    task_id: str
    project_id: str
    task_description: str
    project_context: dict

    # Git state
    repository_path: str
    main_branch: str
    feature_branch: str

    # Planning state
    plan: str
    plan_approved: bool
    plan_feedback: str

    # Development state
    files_modified: list[str]
    files_created: list[str]
    implementation_summary: str

    # Testing state
    test_results: dict
    tests_passed: bool

    # Output
    commit_hash: str
    report: str

    # Control flow
    messages: Annotated[Sequence[str], operator.add]
    current_step: str
    iteration: int
    error: str


class OrchestratorAgent:
    """Main orchestrator that coordinates all sub-agents"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
        )

        self.planner = PlannerAgent(self.llm)
        self.developer = DeveloperAgent(self.llm)
        self.tester = TesterAgent(self.llm)
        self.git_agent = GitAgent()

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("git_sync", self.git_sync_node)
        workflow.add_node("create_branch", self.create_branch_node)
        workflow.add_node("plan", self.plan_node)
        workflow.add_node("wait_approval", self.wait_approval_node)
        workflow.add_node("develop", self.develop_node)
        workflow.add_node("test", self.test_node)
        workflow.add_node("commit_push", self.commit_push_node)
        workflow.add_node("generate_report", self.generate_report_node)

        # Define edges
        workflow.set_entry_point("git_sync")
        workflow.add_edge("git_sync", "create_branch")
        workflow.add_edge("create_branch", "plan")
        workflow.add_edge("plan", "wait_approval")

        # Conditional edge based on approval
        workflow.add_conditional_edges(
            "wait_approval",
            self.approval_router,
            {"approved": "develop", "revise": "plan", "rejected": END},
        )

        workflow.add_edge("develop", "test")

        # Conditional edge based on test results
        workflow.add_conditional_edges(
            "test",
            self.test_router,
            {"passed": "commit_push", "failed": "develop"},  # Retry development
        )

        workflow.add_edge("commit_push", "generate_report")
        workflow.add_edge("generate_report", END)

        return workflow.compile()

    async def git_sync_node(self, state: AgentState) -> AgentState:
        """Sync with main branch"""
        logger.info(f"[{state['task_id']}] Starting git sync")
        state["current_step"] = "git_sync"

        try:
            # Detect main branch
            main_branch = await self.git_agent.detect_main_branch(
                state["repository_path"]
            )
            state["main_branch"] = main_branch

            # Pull latest changes
            await self.git_agent.pull_latest(state["repository_path"], main_branch)

            state["messages"].append(f"✓ Synced with {main_branch} branch")
            logger.info(f"[{state['task_id']}] Git sync completed")

        except Exception as e:
            logger.error(f"[{state['task_id']}] Git sync failed: {e}")
            state["error"] = f"Git sync failed: {str(e)}"

        return state

    async def create_branch_node(self, state: AgentState) -> AgentState:
        """Create a new feature branch"""
        logger.info(f"[{state['task_id']}] Creating feature branch")
        state["current_step"] = "create_branch"

        try:
            # Generate branch name from task description
            branch_name = await self.git_agent.generate_branch_name(
                state["task_description"]
            )
            state["feature_branch"] = branch_name

            # Create and checkout branch
            await self.git_agent.create_branch(state["repository_path"], branch_name)

            state["messages"].append(f"✓ Created branch: {branch_name}")
            logger.info(f"[{state['task_id']}] Branch created: {branch_name}")

        except Exception as e:
            logger.error(f"[{state['task_id']}] Branch creation failed: {e}")
            state["error"] = f"Branch creation failed: {str(e)}"

        return state

    async def plan_node(self, state: AgentState) -> AgentState:
        """Generate implementation plan"""
        logger.info(f"[{state['task_id']}] Generating implementation plan")
        state["current_step"] = "planning"

        try:
            # Load project memory for context
            memory = ProjectMemory(state["project_id"])
            project_context = await memory.get_context()

            # Generate plan
            plan = await self.planner.create_plan(
                task_description=state["task_description"],
                project_context=project_context,
                repository_path=state["repository_path"],
                feedback=state.get("plan_feedback"),
            )

            state["plan"] = plan
            state["messages"].append("✓ Implementation plan generated")
            logger.info(f"[{state['task_id']}] Plan generated successfully")

        except Exception as e:
            logger.error(f"[{state['task_id']}] Planning failed: {e}")
            state["error"] = f"Planning failed: {str(e)}"

        return state

    async def wait_approval_node(self, state: AgentState) -> AgentState:
        """Wait for human approval"""
        logger.info(f"[{state['task_id']}] Waiting for approval")
        state["current_step"] = "awaiting_approval"
        state["messages"].append("⏳ Waiting for plan approval...")

        # This node just sets the state
        # Actual approval comes from API endpoint
        return state

    def approval_router(self, state: AgentState) -> str:
        """Route based on approval status"""
        if state.get("plan_approved"):
            return "approved"
        elif state.get("plan_feedback"):
            return "revise"
        else:
            return "rejected"

    async def develop_node(self, state: AgentState) -> AgentState:
        """Implement the feature"""
        logger.info(f"[{state['task_id']}] Starting development")
        state["current_step"] = "in_progress"

        try:
            # Load project memory
            memory = ProjectMemory(state["project_id"])
            project_context = await memory.get_context()

            # Implement based on plan
            result = await self.developer.implement(
                plan=state["plan"],
                project_context=project_context,
                repository_path=state["repository_path"],
            )

            state["files_modified"] = result["files_modified"]
            state["files_created"] = result["files_created"]
            state["implementation_summary"] = result["summary"]
            state["messages"].append("✓ Implementation completed")

            logger.info(f"[{state['task_id']}] Development completed")

        except Exception as e:
            logger.error(f"[{state['task_id']}] Development failed: {e}")
            state["error"] = f"Development failed: {str(e)}"

        return state

    async def test_node(self, state: AgentState) -> AgentState:
        """Test the implementation"""
        logger.info(f"[{state['task_id']}] Running tests")
        state["current_step"] = "testing"

        try:
            # Run tests
            test_results = await self.tester.run_tests(
                repository_path=state["repository_path"],
                files_modified=state["files_modified"],
                files_created=state["files_created"],
            )

            state["test_results"] = test_results
            state["tests_passed"] = test_results["all_passed"]

            if test_results["all_passed"]:
                state["messages"].append("✓ All tests passed")
            else:
                state["messages"].append("⚠ Some tests failed, retrying development...")

            logger.info(f"[{state['task_id']}] Testing completed")

        except Exception as e:
            logger.error(f"[{state['task_id']}] Testing failed: {e}")
            state["error"] = f"Testing failed: {str(e)}"

        return state

    def test_router(self, state: AgentState) -> str:
        """Route based on test results"""
        if state.get("tests_passed"):
            return "passed"
        elif state.get("iteration", 0) < settings.MAX_ITERATIONS:
            state["iteration"] = state.get("iteration", 0) + 1
            return "failed"
        else:
            state["error"] = "Max iterations reached with failing tests"
            return "passed"  # Proceed anyway but with error

    async def commit_push_node(self, state: AgentState) -> AgentState:
        """Commit and push changes"""
        logger.info(f"[{state['task_id']}] Committing and pushing")
        state["current_step"] = "commit_push"

        try:
            # Generate commit message
            commit_message = await self.git_agent.generate_commit_message(
                state["task_description"],
                state["files_modified"],
                state["files_created"],
            )

            # Commit changes
            commit_hash = await self.git_agent.commit_and_push(
                state["repository_path"], state["feature_branch"], commit_message
            )

            state["commit_hash"] = commit_hash
            state["messages"].append(f"✓ Pushed to {state['feature_branch']}")

            logger.info(f"[{state['task_id']}] Commit pushed: {commit_hash}")

        except Exception as e:
            logger.error(f"[{state['task_id']}] Commit/push failed: {e}")
            state["error"] = f"Commit/push failed: {str(e)}"

        return state

    async def generate_report_node(self, state: AgentState) -> AgentState:
        """Generate completion report"""
        logger.info(f"[{state['task_id']}] Generating report")
        state["current_step"] = "completed"

        try:
            # Generate comprehensive report
            report = await self.planner.generate_report(
                task_description=state["task_description"],
                plan=state["plan"],
                implementation_summary=state["implementation_summary"],
                test_results=state["test_results"],
                commit_hash=state["commit_hash"],
                branch_name=state["feature_branch"],
            )

            state["report"] = report
            state["messages"].append("✓ Task completed successfully!")

            logger.info(f"[{state['task_id']}] Report generated")

        except Exception as e:
            logger.error(f"[{state['task_id']}] Report generation failed: {e}")
            state["error"] = f"Report generation failed: {str(e)}"

        return state

    async def execute(self, initial_state: AgentState) -> AgentState:
        """Execute the entire workflow"""
        logger.info(f"[{initial_state['task_id']}] Starting orchestrator execution")

        # Initialize state
        initial_state.setdefault("messages", [])
        initial_state.setdefault("iteration", 0)
        initial_state.setdefault("current_step", "starting")

        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            return final_state

        except Exception as e:
            logger.error(f"[{initial_state['task_id']}] Orchestrator failed: {e}")
            initial_state["error"] = str(e)
            initial_state["current_step"] = "failed"
            return initial_state
