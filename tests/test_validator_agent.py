"""Tests for ValidatorAgent"""
import pytest
from unittest.mock import Mock, AsyncMock
import json
from pathlib import Path
from app.agents.validator_agent import ValidatorAgent


@pytest.fixture
def mock_llm():
    """Mock LangChain LLM"""
    llm = Mock()
    llm.ainvoke = AsyncMock()
    return llm


@pytest.fixture
def validator_agent(mock_llm):
    """Create ValidatorAgent instance"""
    return ValidatorAgent(mock_llm)


@pytest.mark.asyncio
async def test_validate_plan_success(validator_agent, mock_llm):
    """Test successful plan validation"""
    # Arrange
    validation_result = {
        "is_valid": True,
        "coverage_score": 95,
        "issues": [],
        "missing_requirements": [],
        "recommendations": ["Good plan!"],
        "summary": "Plan looks good",
    }

    mock_response = Mock()
    mock_response.content = json.dumps(validation_result)
    mock_llm.ainvoke.return_value = mock_response

    plan = "# Plan\n\nDetailed implementation..."
    task_description = "Add authentication with JWT"
    codebase_info = {"existing_patterns": ["api-pattern"], "test_directories": ["tests"]}

    # Act
    result = await validator_agent.validate_plan(plan, task_description, codebase_info)

    # Assert
    assert result["is_valid"] is True
    assert result["coverage_score"] == 95
    assert len(result["issues"]) == 0
    assert mock_llm.ainvoke.called


@pytest.mark.asyncio
async def test_validate_plan_with_issues(validator_agent, mock_llm):
    """Test plan validation with issues"""
    # Arrange
    validation_result = {
        "is_valid": False,
        "coverage_score": 60,
        "issues": [
            {
                "severity": "critical",
                "category": "requirement_coverage",
                "message": "Missing authentication requirement",
            }
        ],
        "missing_requirements": ["JWT token generation"],
        "recommendations": ["Add JWT implementation"],
        "summary": "Plan incomplete",
    }

    mock_response = Mock()
    mock_response.content = json.dumps(validation_result)
    mock_llm.ainvoke.return_value = mock_response

    # Act
    result = await validator_agent.validate_plan("plan", "task", {})

    # Assert
    assert result["is_valid"] is False
    assert result["coverage_score"] == 60
    assert len(result["issues"]) == 1
    assert result["issues"][0]["severity"] == "critical"
    assert len(result["missing_requirements"]) == 1


@pytest.mark.asyncio
async def test_validate_plan_with_markdown_json(validator_agent, mock_llm):
    """Test validation with JSON in markdown code blocks"""
    # Arrange
    validation_result = {"is_valid": True, "coverage_score": 85, "issues": [], "missing_requirements": [], "recommendations": [], "summary": "OK"}

    mock_response = Mock()
    mock_response.content = f"```json\n{json.dumps(validation_result)}\n```"
    mock_llm.ainvoke.return_value = mock_response

    # Act
    result = await validator_agent.validate_plan("plan", "task", {})

    # Assert
    assert result["is_valid"] is True
    assert result["coverage_score"] == 85


@pytest.mark.asyncio
async def test_validate_plan_error_handling(validator_agent, mock_llm):
    """Test error handling in plan validation"""
    # Arrange
    mock_llm.ainvoke.side_effect = Exception("API Error")

    # Act
    result = await validator_agent.validate_plan("plan", "task", {})

    # Assert - should return default passing result with warning
    assert result["is_valid"] is True
    assert result["coverage_score"] == 50
    assert len(result["issues"]) > 0
    assert "error" in result["issues"][0]["message"].lower()


@pytest.mark.asyncio
async def test_validate_implementation_success(validator_agent, mock_llm, tmp_path):
    """Test successful implementation validation"""
    # Arrange
    validation_result = {
        "is_valid": True,
        "adherence_score": 90,
        "issues": [],
        "missing_files": [],
        "quality_concerns": [],
        "summary": "Implementation looks good",
    }

    mock_response = Mock()
    mock_response.content = json.dumps(validation_result)
    mock_llm.ainvoke.return_value = mock_response

    # Create a sample file
    (tmp_path / "app").mkdir()
    test_file = tmp_path / "app" / "auth.py"
    test_file.write_text("def authenticate(): pass")

    # Act
    result = await validator_agent.validate_implementation(
        plan="Plan content",
        task_description="Add auth",
        files_created=["app/auth.py"],
        files_modified=[],
        repository_path=tmp_path,
    )

    # Assert
    assert result["is_valid"] is True
    assert result["adherence_score"] == 90
    assert mock_llm.ainvoke.called


@pytest.mark.asyncio
async def test_validate_implementation_with_concerns(validator_agent, mock_llm, tmp_path):
    """Test implementation validation with quality concerns"""
    # Arrange
    validation_result = {
        "is_valid": True,
        "adherence_score": 70,
        "issues": [
            {
                "severity": "warning",
                "category": "quality",
                "message": "Missing error handling",
            }
        ],
        "missing_files": [],
        "quality_concerns": ["No docstrings", "No type hints"],
        "summary": "Implementation needs improvement",
    }

    mock_response = Mock()
    mock_response.content = json.dumps(validation_result)
    mock_llm.ainvoke.return_value = mock_response

    # Act
    result = await validator_agent.validate_implementation(
        plan="Plan",
        task_description="Task",
        files_created=["file.py"],
        files_modified=[],
        repository_path=tmp_path,
    )

    # Assert
    assert len(result["quality_concerns"]) == 2
    assert result["adherence_score"] == 70
