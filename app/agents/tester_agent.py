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
            prompt = f"""You are an expert at writing unit tests. Generate comprehensive pytest tests for the following code.

FILE: {file_path}

CODE:
```python
{code[:2000]}  # Limit to avoid token limits
```

REQUIREMENTS:
1. Use pytest framework
2. Test all public functions and classes
3. Include edge cases and error conditions
4. Use proper fixtures if needed
5. Add docstrings to test functions
6. Make tests independent and isolated
7. Include both positive and negative test cases

Generate ONLY the complete test file code, no explanations:
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
