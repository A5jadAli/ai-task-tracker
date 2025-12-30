from langchain_openai import ChatOpenAI
from pathlib import Path
from typing import Dict, List
from loguru import logger
import subprocess
import os


class TesterAgent:
    """Agent responsible for testing implementations"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def run_tests(
        self, repository_path: Path, files_modified: List[str], files_created: List[str]
    ) -> Dict:
        """Run tests on the implementation"""
        try:
            logger.info("Starting testing phase")

            test_results = {
                "all_passed": True,
                "passed": 0,
                "failed": 0,
                "total": 0,
                "output": "",
                "details": [],
            }

            # Step 1: Generate tests for new files
            generated_tests = await self._generate_tests(
                repository_path=repository_path,
                files_created=files_created,
                files_modified=files_modified,
            )

            test_results["details"].append(
                f"Generated {len(generated_tests)} test files"
            )

            # Step 2: Run existing test suite
            existing_test_result = await self._run_existing_tests(repository_path)
            test_results["details"].append(
                f"Existing tests: {existing_test_result['summary']}"
            )

            # Step 3: Run newly generated tests
            if generated_tests:
                new_test_result = await self._run_new_tests(
                    repository_path, generated_tests
                )
                test_results["details"].append(
                    f"New tests: {new_test_result['summary']}"
                )
            else:
                new_test_result = {
                    "passed": 0,
                    "failed": 0,
                    "output": "No new tests generated",
                }

            # Step 4: Run static analysis (linting, type checking)
            static_analysis = await self._run_static_analysis(
                repository_path, files_created + files_modified
            )
            test_results["details"].append(
                f"Static analysis: {static_analysis['summary']}"
            )

            # Aggregate results
            test_results["passed"] = existing_test_result.get(
                "passed", 0
            ) + new_test_result.get("passed", 0)
            test_results["failed"] = existing_test_result.get(
                "failed", 0
            ) + new_test_result.get("failed", 0)
            test_results["total"] = test_results["passed"] + test_results["failed"]

            # Combine outputs
            outputs = []
            if existing_test_result.get("output"):
                outputs.append(
                    "=== Existing Tests ===\n" + existing_test_result["output"]
                )
            if new_test_result.get("output"):
                outputs.append("=== New Tests ===\n" + new_test_result["output"])
            if static_analysis.get("output"):
                outputs.append("=== Static Analysis ===\n" + static_analysis["output"])

            test_results["output"] = "\n\n".join(outputs)

            # Determine overall pass/fail
            test_results["all_passed"] = test_results[
                "failed"
            ] == 0 and not static_analysis.get("has_errors", False)

            logger.info(
                f"Testing completed: {test_results['passed']} passed, {test_results['failed']} failed"
            )

            return test_results

        except Exception as e:
            logger.error(f"Testing failed: {e}")
            return {
                "all_passed": False,
                "passed": 0,
                "failed": 1,
                "total": 1,
                "output": f"Testing error: {str(e)}",
                "details": [f"Error: {str(e)}"],
            }

    async def _generate_tests(
        self, repository_path: Path, files_created: List[str], files_modified: List[str]
    ) -> List[Dict]:
        """Generate test files for new/modified code"""
        try:
            logger.info("Generating tests for new/modified files")

            generated_tests = []

            # Focus on newly created Python files
            python_files = [
                f
                for f in files_created
                if f.endswith(".py") and not f.startswith("test_")
            ]

            for file_path in python_files[
                :5
            ]:  # Limit to 5 files to avoid too many tests
                try:
                    full_path = repository_path / file_path
                    if not full_path.exists():
                        continue

                    # Read the code
                    code = full_path.read_text(encoding="utf-8")

                    # Generate test
                    test_code = await self._generate_test_for_file(file_path, code)

                    # Determine test file path
                    test_file_path = self._get_test_file_path(file_path)
                    test_full_path = repository_path / test_file_path

                    # Create test file
                    test_full_path.parent.mkdir(parents=True, exist_ok=True)
                    test_full_path.write_text(test_code, encoding="utf-8")

                    generated_tests.append(
                        {"source_file": file_path, "test_file": test_file_path}
                    )

                    logger.info(f"Generated test for {file_path} -> {test_file_path}")

                except Exception as e:
                    logger.warning(f"Could not generate test for {file_path}: {e}")

            return generated_tests

        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return []

    async def _generate_test_for_file(self, file_path: str, code: str) -> str:
        """Generate test code for a specific file"""
        try:
            # Determine test type based on file content
            is_api = "APIRouter" in code or "FastAPI" in code or "@app" in code or "@router" in code
            is_service = "service" in file_path.lower() or "class" in code.lower()
            is_model = "BaseModel" in code or "SQLModel" in code or "models" in file_path.lower()

            test_type_guidance = ""
            if is_api:
                test_type_guidance = """
## API/ROUTE TESTING GUIDANCE
- Use FastAPI TestClient for endpoint testing
- Test all HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Test success responses (200, 201, 204)
- Test error responses (400, 404, 500)
- Test authentication/authorization if present
- Test request validation (valid/invalid data)
- Test edge cases (empty data, wrong types, missing fields)
- Mock dependencies and database calls
"""
            elif is_service:
                test_type_guidance = """
## SERVICE/BUSINESS LOGIC TESTING GUIDANCE
- Test all public methods
- Mock external dependencies (database, APIs, file system)
- Test happy path and error scenarios
- Test with various input combinations
- Verify correct exception handling
- Test async methods properly with pytest-asyncio
"""
            elif is_model:
                test_type_guidance = """
## MODEL/SCHEMA TESTING GUIDANCE
- Test model validation (valid/invalid data)
- Test required vs optional fields
- Test field constraints (min/max, regex, etc.)
- Test serialization/deserialization
- Test relationships if database model
"""

            prompt = f"""You are an expert at writing comprehensive tests. Generate production-quality pytest tests for the following code.

## FILE TO TEST
{file_path}

## CODE TO TEST
```python
{code[:3000]}  # Increased limit for better context
```

{test_type_guidance}

## CRITICAL TESTING REQUIREMENTS
1. Use pytest framework with modern best practices
2. Import and test ALL public functions, classes, and methods
3. Create comprehensive test coverage:
   - Happy path (successful execution)
   - Edge cases (boundary values, empty inputs, None values)
   - Error cases (exceptions, invalid inputs, failed operations)
   - Integration scenarios if applicable

4. Use proper pytest features:
   - fixtures for setup/teardown
   - parametrize for multiple test cases
   - marks (@pytest.mark.asyncio for async tests)
   - mocking with pytest-mock or unittest.mock

5. Test structure:
   - One test class per class being tested (if applicable)
   - Clear, descriptive test names (test_function_name_when_condition_then_result)
   - Arrange-Act-Assert pattern
   - Independent tests (no test depends on another)

6. For API endpoints test:
   - All HTTP status codes
   - Request/response validation
   - Authentication/authorization
   - Error handling

7. For services test:
   - All public methods
   - Success and failure scenarios
   - Exception handling
   - Mock external dependencies

8. For models test:
   - Field validation
   - Required vs optional fields
   - Data type constraints
   - Custom validators

9. Code quality:
   - Add docstrings to test functions
   - Use clear assertion messages
   - Proper type hints
   - Mock external dependencies (DB, APIs, files)

10. Coverage goals:
   - Aim for 100% coverage of public interfaces
   - Test all code paths
   - Test all error conditions

## EXAMPLE STRUCTURE
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient  # for API tests
import asyncio  # for async tests

# Import what you're testing
from your_module import YourClass, your_function

@pytest.fixture
def sample_data():
    \"\"\"Fixture for test data\"\"\"
    return {{"key": "value"}}

class TestYourClass:
    \"\"\"Test suite for YourClass\"\"\"

    def test_method_success(self, sample_data):
        \"\"\"Test method_name succeeds with valid input\"\"\"
        # Arrange
        obj = YourClass()

        # Act
        result = obj.method_name(sample_data)

        # Assert
        assert result is not None
        assert result["key"] == "value"

    def test_method_with_invalid_input_raises_error(self):
        \"\"\"Test method_name raises ValueError for invalid input\"\"\"
        obj = YourClass()

        with pytest.raises(ValueError):
            obj.method_name(None)
```

Generate ONLY the complete, production-ready test file code.
Do not include explanations or markdown.
Output raw Python code that can be directly saved to a file:
"""

            response = await self.llm.ainvoke(prompt)
            test_code = response.content.strip()

            # Remove markdown if present
            if test_code.startswith("```"):
                lines = test_code.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                test_code = "\n".join(lines)

            return test_code

        except Exception as e:
            logger.error(f"Failed to generate test: {e}")
            raise

    def _get_test_file_path(self, source_file: str) -> str:
        """Generate test file path from source file path"""
        path = Path(source_file)

        # If already in tests directory, keep it there
        if "tests" in path.parts or "test" in path.parts:
            filename = f"test_{path.stem}{path.suffix}"
            return str(path.parent / filename)

        # Otherwise, create in tests directory
        filename = f"test_{path.stem}{path.suffix}"
        return str(Path("tests") / filename)

    async def _run_existing_tests(self, repository_path: Path) -> Dict:
        """Run existing test suite"""
        try:
            logger.info("Running existing tests")

            # Check if pytest is available
            result = subprocess.run(
                ["pytest", "--version"],
                cwd=repository_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.warning("pytest not available, skipping existing tests")
                return {
                    "passed": 0,
                    "failed": 0,
                    "output": "pytest not installed",
                    "summary": "skipped (pytest not available)",
                }

            # Run pytest
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                cwd=repository_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            output = result.stdout + result.stderr

            # Parse results
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")

            logger.info(f"Existing tests: {passed} passed, {failed} failed")

            return {
                "passed": passed,
                "failed": failed,
                "output": output[-2000:],  # Last 2000 chars
                "summary": f"{passed} passed, {failed} failed",
            }

        except subprocess.TimeoutExpired:
            logger.error("Existing tests timed out")
            return {
                "passed": 0,
                "failed": 1,
                "output": "Tests timed out after 5 minutes",
                "summary": "timeout",
            }
        except Exception as e:
            logger.warning(f"Could not run existing tests: {e}")
            return {
                "passed": 0,
                "failed": 0,
                "output": f"Error: {str(e)}",
                "summary": "error",
            }

    async def _run_new_tests(
        self, repository_path: Path, generated_tests: List[Dict]
    ) -> Dict:
        """Run newly generated tests"""
        try:
            logger.info("Running newly generated tests")

            # Get list of test files
            test_files = [t["test_file"] for t in generated_tests]

            if not test_files:
                return {
                    "passed": 0,
                    "failed": 0,
                    "output": "No test files to run",
                    "summary": "no tests",
                }

            # Run pytest on specific test files
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"] + test_files,
                cwd=repository_path,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minute timeout
            )

            output = result.stdout + result.stderr

            # Parse results
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")

            logger.info(f"New tests: {passed} passed, {failed} failed")

            return {
                "passed": passed,
                "failed": failed,
                "output": output[-2000:],
                "summary": f"{passed} passed, {failed} failed",
            }

        except subprocess.TimeoutExpired:
            logger.error("New tests timed out")
            return {
                "passed": 0,
                "failed": 1,
                "output": "New tests timed out",
                "summary": "timeout",
            }
        except Exception as e:
            logger.warning(f"Could not run new tests: {e}")
            return {
                "passed": 0,
                "failed": 0,
                "output": f"Error: {str(e)}",
                "summary": "error",
            }

    async def _run_static_analysis(
        self, repository_path: Path, files: List[str]
    ) -> Dict:
        """Run static analysis (linting, type checking)"""
        try:
            logger.info("Running static analysis")

            results = []
            has_errors = False

            # Try flake8 for linting
            try:
                result = subprocess.run(
                    ["flake8"] + files,
                    cwd=repository_path,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0:
                    has_errors = True
                    results.append(f"Linting issues found:\n{result.stdout[:500]}")
                else:
                    results.append("✓ Linting passed")

            except (subprocess.TimeoutExpired, FileNotFoundError):
                results.append("⊘ Linting skipped (flake8 not available)")

            # Try mypy for type checking (only for Python files)
            python_files = [f for f in files if f.endswith(".py")]
            if python_files:
                try:
                    result = subprocess.run(
                        ["mypy", "--ignore-missing-imports"] + python_files[:5],
                        cwd=repository_path,
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )

                    if "error" in result.stdout.lower():
                        results.append(f"Type checking issues:\n{result.stdout[:500]}")
                    else:
                        results.append("✓ Type checking passed")

                except (subprocess.TimeoutExpired, FileNotFoundError):
                    results.append("⊘ Type checking skipped (mypy not available)")

            output = "\n".join(results)
            summary = f"{'issues found' if has_errors else 'passed'}"

            logger.info(f"Static analysis: {summary}")

            return {"has_errors": has_errors, "output": output, "summary": summary}

        except Exception as e:
            logger.warning(f"Static analysis failed: {e}")
            return {
                "has_errors": False,
                "output": f"Static analysis error: {str(e)}",
                "summary": "error",
            }
