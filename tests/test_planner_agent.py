"""Tests for PlannerAgent"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from app.agents.planner_agent import PlannerAgent


@pytest.fixture
def mock_llm():
    """Mock LangChain LLM"""
    llm = Mock()
    llm.ainvoke = AsyncMock()
    return llm


@pytest.fixture
def planner_agent(mock_llm):
    """Create PlannerAgent instance"""
    return PlannerAgent(mock_llm)


@pytest.mark.asyncio
async def test_create_plan_success(planner_agent, mock_llm, tmp_path):
    """Test successful plan creation"""
    # Arrange
    mock_response = Mock()
    mock_response.content = "# Implementation Plan\n\nThis is a test plan"
    mock_llm.ainvoke.return_value = mock_response

    task_description = "Add user authentication"
    project_context = {"tech_stack": "FastAPI", "coding_style": "PEP 8"}

    # Act
    plan = await planner_agent.create_plan(
        task_description=task_description,
        project_context=project_context,
        repository_path=tmp_path,
    )

    # Assert
    assert plan == "# Implementation Plan\n\nThis is a test plan"
    assert mock_llm.ainvoke.called
    call_args = mock_llm.ainvoke.call_args[0][0]
    assert "Add user authentication" in call_args
    assert "FastAPI" in call_args


@pytest.mark.asyncio
async def test_create_plan_with_feedback(planner_agent, mock_llm, tmp_path):
    """Test plan creation with feedback"""
    # Arrange
    mock_response = Mock()
    mock_response.content = "# Revised Plan"
    mock_llm.ainvoke.return_value = mock_response

    feedback = "Please add more detail about error handling"

    # Act
    plan = await planner_agent.create_plan(
        task_description="Add feature",
        project_context={},
        repository_path=tmp_path,
        feedback=feedback,
    )

    # Assert
    assert plan == "# Revised Plan"
    call_args = mock_llm.ainvoke.call_args[0][0]
    assert feedback in call_args


@pytest.mark.asyncio
async def test_analyze_codebase(planner_agent, tmp_path):
    """Test codebase analysis"""
    # Arrange - create sample project structure
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("print('hello')")
    (tmp_path / "app" / "api").mkdir()
    (tmp_path / "app" / "models").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "requirements.txt").write_text("fastapi==0.109.0")

    # Act
    info = await planner_agent._analyze_codebase(tmp_path)

    # Assert
    assert info["file_count"] > 0
    assert "Python" in info["languages"]
    assert len(info["main_files"]) > 0
    assert "app-directory-pattern" in info["existing_patterns"]
    assert "api-directory-pattern" in info["existing_patterns"]
    assert "models-pattern" in info["existing_patterns"]
    assert "has-tests" in info["existing_patterns"]


@pytest.mark.asyncio
async def test_save_plan(planner_agent, tmp_path):
    """Test plan saving"""
    # Arrange
    plan_content = "# Test Plan\n\nImplementation details..."
    task_id = "test-task-123"

    # Act
    plan_path = await planner_agent.save_plan(
        plan=plan_content, task_id=task_id, plans_dir=tmp_path
    )

    # Assert
    assert Path(plan_path).exists()
    assert Path(plan_path).read_text() == plan_content
    assert task_id in plan_path


@pytest.mark.asyncio
async def test_generate_report(planner_agent, mock_llm):
    """Test report generation"""
    # Arrange
    mock_response = Mock()
    mock_response.content = "# Completion Report\n\nTask completed successfully"
    mock_llm.ainvoke.return_value = mock_response

    test_results = {"passed": 10, "failed": 0, "total": 10, "output": "All passed"}

    # Act
    report = await planner_agent.generate_report(
        task_description="Add authentication",
        plan="Original plan",
        implementation_summary="Added auth endpoints",
        test_results=test_results,
        commit_hash="abc123",
        branch_name="feature/auth",
    )

    # Assert
    assert "Completion Report" in report
    assert mock_llm.ainvoke.called
    call_args = mock_llm.ainvoke.call_args[0][0]
    assert "10" in call_args  # Test count
    assert "abc123" in call_args


def test_detect_patterns(planner_agent):
    """Test pattern detection from directory structure"""
    # Arrange
    dir_structure = {
        "app": ["main.py"],
        "app/api": ["routes.py"],
        "app/models": ["user.py"],
        "app/services": ["auth.py"],
        "tests": ["test_api.py"],
    }

    # Act
    patterns = planner_agent._detect_patterns(dir_structure)

    # Assert
    assert "app-directory-pattern" in patterns
    assert "api-directory-pattern" in patterns
    assert "models-pattern" in patterns
    assert "services-pattern" in patterns
    assert "has-tests" in patterns
    assert "routes-pattern" in patterns
