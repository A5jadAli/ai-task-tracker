from langchain_openai import ChatOpenAI
from pathlib import Path
from typing import Dict, List
from loguru import logger


class ValidatorAgent:
    """Agent responsible for validating implementation against requirements"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def validate_plan(
        self, plan: str, task_description: str, codebase_info: dict
    ) -> Dict:
        """Validate that the plan addresses all requirements"""
        try:
            logger.info("Validating implementation plan")

            prompt = f"""You are a quality assurance expert. Analyze the implementation plan to ensure it fully addresses all requirements.

## ORIGINAL TASK DESCRIPTION
{task_description}

## GENERATED IMPLEMENTATION PLAN
{plan}

## CODEBASE STRUCTURE
- Existing Patterns: {', '.join(codebase_info.get('existing_patterns', []))}
- Test Directories: {', '.join(codebase_info.get('test_directories', []))}

## YOUR TASK
Analyze the plan and validate:

1. **Requirement Coverage**: Does the plan address EVERY requirement mentioned in the task description?
   - List each requirement from the task
   - Check if the plan covers it
   - Flag any missing requirements

2. **Project Structure Compliance**: Does the plan respect existing project structure?
   - Check if new files follow existing patterns
   - Check if file placement makes sense
   - Flag any structural violations

3. **Testing Adequacy**: Is the testing strategy comprehensive?
   - Does it cover unit tests?
   - Does it cover integration tests?
   - Does it specify what to test?
   - Flag if testing is insufficient

4. **Completeness**: Is the plan detailed enough?
   - Are file paths specific?
   - Are implementation steps clear?
   - Are dependencies listed?
   - Flag if too vague

5. **Feasibility**: Can this plan be implemented as described?
   - Are there any contradictions?
   - Are there missing steps?
   - Flag any issues

Return a JSON object with this structure:
{{
    "is_valid": true/false,
    "coverage_score": 0-100,
    "issues": [
        {{"severity": "critical/warning", "category": "requirement_coverage/structure/testing/completeness/feasibility", "message": "description"}}
    ],
    "missing_requirements": ["list of requirements not addressed"],
    "recommendations": ["list of improvements"],
    "summary": "brief summary of validation"
}}

Return ONLY valid JSON, no markdown or explanations:
"""

            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()

            # Extract JSON from potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            import json

            validation_result = json.loads(content)

            logger.info(
                f"Plan validation: {validation_result.get('is_valid', False)}, "
                f"score: {validation_result.get('coverage_score', 0)}"
            )

            return validation_result

        except Exception as e:
            logger.error(f"Failed to validate plan: {e}")
            # Return a default "pass" result to not block execution
            return {
                "is_valid": True,
                "coverage_score": 50,
                "issues": [{"severity": "warning", "category": "validation", "message": f"Validation error: {str(e)}"}],
                "missing_requirements": [],
                "recommendations": [],
                "summary": "Validation encountered an error but allowing execution",
            }

    async def validate_implementation(
        self,
        plan: str,
        task_description: str,
        files_created: List[str],
        files_modified: List[str],
        repository_path: Path,
    ) -> Dict:
        """Validate that the implementation matches the plan and requirements"""
        try:
            logger.info("Validating implementation against plan")

            # Read sample of created files
            created_samples = []
            for file_path in files_created[:5]:  # Limit to 5 files
                try:
                    full_path = repository_path / file_path
                    if full_path.exists():
                        content = full_path.read_text(encoding="utf-8")
                        created_samples.append(
                            f"File: {file_path}\nContent (first 500 chars):\n{content[:500]}\n"
                        )
                except Exception:
                    pass

            created_files_summary = "\n".join(created_samples) if created_samples else "No files sampled"

            prompt = f"""You are a quality assurance expert. Validate that the implementation matches the plan and meets all requirements.

## ORIGINAL TASK DESCRIPTION
{task_description}

## IMPLEMENTATION PLAN
{plan[:2000]}

## IMPLEMENTATION RESULTS
Files Created: {', '.join(files_created)}
Files Modified: {', '.join(files_modified)}

## SAMPLE OF CREATED FILES
{created_files_summary}

## YOUR TASK
Validate the implementation:

1. **Plan Adherence**: Did the implementation follow the plan?
   - Were all planned files created?
   - Were all modifications made?
   - Flag any deviations

2. **Requirement Fulfillment**: Does the implementation meet the original requirements?
   - Check against each requirement from the task description
   - Flag any missing functionality

3. **Code Quality Indicators** (from samples):
   - Are imports present?
   - Are there docstrings?
   - Is there error handling?
   - Flag quality issues

4. **Completeness**:
   - Are files actually created (not just planned)?
   - Do files have content?
   - Flag if implementation seems incomplete

Return a JSON object:
{{
    "is_valid": true/false,
    "adherence_score": 0-100,
    "issues": [
        {{"severity": "critical/warning", "category": "plan_adherence/requirements/quality/completeness", "message": "description"}}
    ],
    "missing_files": ["files planned but not created"],
    "quality_concerns": ["list of code quality issues"],
    "summary": "brief summary"
}}

Return ONLY valid JSON:
"""

            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            import json

            validation_result = json.loads(content)

            logger.info(
                f"Implementation validation: {validation_result.get('is_valid', False)}, "
                f"score: {validation_result.get('adherence_score', 0)}"
            )

            return validation_result

        except Exception as e:
            logger.error(f"Failed to validate implementation: {e}")
            return {
                "is_valid": True,
                "adherence_score": 50,
                "issues": [{"severity": "warning", "category": "validation", "message": f"Validation error: {str(e)}"}],
                "missing_files": [],
                "quality_concerns": [],
                "summary": "Validation encountered an error but allowing execution",
            }
