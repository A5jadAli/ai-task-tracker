from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pathlib import Path
from typing import Optional, Dict, List
from loguru import logger
import os
from datetime import datetime


class PlannerAgent:
    """Agent responsible for creating implementation plans"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def create_plan(
        self,
        task_description: str,
        project_context: dict,
        repository_path: Path,
        feedback: Optional[str] = None,
    ) -> str:
        """Create a detailed implementation plan"""
        try:
            logger.info("Creating implementation plan")

            # Analyze codebase structure
            codebase_info = await self._analyze_codebase(repository_path)

            # Create planning prompt
            prompt = self._build_planning_prompt(
                task_description=task_description,
                project_context=project_context,
                codebase_info=codebase_info,
                feedback=feedback,
            )

            # Generate plan using LLM
            response = await self.llm.ainvoke(prompt)
            plan = response.content

            logger.info("Implementation plan created successfully")
            return plan

        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            raise Exception(f"Planning failed: {str(e)}")

    def _build_planning_prompt(
        self,
        task_description: str,
        project_context: dict,
        codebase_info: dict,
        feedback: Optional[str] = None,
    ) -> str:
        """Build the planning prompt for the LLM"""

        feedback_section = ""
        if feedback:
            feedback_section = f"""
## FEEDBACK FROM PREVIOUS PLAN
The user provided the following feedback on the previous plan:
{feedback}

Please revise the plan based on this feedback.
"""

        prompt = f"""You are an expert software architect and developer. Create a detailed implementation plan for the following task.

## TASK DESCRIPTION
{task_description}

## PROJECT CONTEXT
- Tech Stack: {project_context.get('tech_stack', 'Not specified')}
- Coding Style: {project_context.get('coding_style', 'Not specified')}
- Test Framework: {project_context.get('test_framework', 'pytest')}
- Additional Context: {project_context.get('additional_info', 'None')}

## CODEBASE STRUCTURE
- Root Directory: {codebase_info.get('root_dir', 'Unknown')}
- Main Files: {', '.join(codebase_info.get('main_files', [])[:10])}
- Total Files: {codebase_info.get('file_count', 0)}
- Languages Detected: {', '.join(codebase_info.get('languages', ['Python']))}

{feedback_section}

## YOUR TASK
Create a comprehensive implementation plan in Markdown format that includes:

1. **Summary**: Brief overview of what will be implemented (2-3 sentences)

2. **Objectives**: Clear, measurable objectives for this task

3. **Files to Modify**: List existing files that need changes and what changes are needed

4. **Files to Create**: List new files that need to be created and their purpose

5. **Implementation Steps**: Detailed, numbered steps to implement the feature

6. **Dependencies**: Any new packages or libraries that need to be installed

7. **Testing Strategy**: How the implementation will be tested (unit tests, integration tests, etc.)

8. **Risks & Considerations**: Potential issues or edge cases to be aware of

9. **Estimated Time**: Rough estimate of implementation time

10. **Questions for Review**: Any ambiguities or decisions that need human input

## FORMAT
Use proper Markdown formatting with headers (##), bullet points, and code blocks where appropriate.
Be specific and actionable - this plan will be used by another AI agent to implement the code.

Generate the plan now:
"""
        return prompt

    async def _analyze_codebase(self, repository_path: Path) -> dict:
        """Analyze the codebase structure"""
        try:
            info = {
                "root_dir": str(repository_path),
                "main_files": [],
                "file_count": 0,
                "languages": set(),
            }

            # Walk through the repository
            for root, dirs, files in os.walk(repository_path):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "__pycache__", "venv", "env"]
                ]

                for file in files:
                    if file.startswith("."):
                        continue

                    info["file_count"] += 1
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(repository_path)

                    # Collect main files (config, main entry points, etc.)
                    if file in [
                        "main.py",
                        "app.py",
                        "index.js",
                        "package.json",
                        "requirements.txt",
                        "setup.py",
                        "README.md",
                    ]:
                        info["main_files"].append(str(relative_path))

                    # Detect languages
                    extension = file_path.suffix.lower()
                    if extension in [".py"]:
                        info["languages"].add("Python")
                    elif extension in [".js", ".jsx", ".ts", ".tsx"]:
                        info["languages"].add("JavaScript/TypeScript")
                    elif extension in [".java"]:
                        info["languages"].add("Java")
                    elif extension in [".go"]:
                        info["languages"].add("Go")
                    elif extension in [".rs"]:
                        info["languages"].add("Rust")

            info["languages"] = list(info["languages"])
            logger.info(
                f"Analyzed codebase: {info['file_count']} files, languages: {info['languages']}"
            )

            return info

        except Exception as e:
            logger.error(f"Failed to analyze codebase: {e}")
            return {
                "root_dir": str(repository_path),
                "main_files": [],
                "file_count": 0,
                "languages": ["Python"],
            }

    async def save_plan(self, plan: str, task_id: str, plans_dir: Path) -> str:
        """Save the plan to a markdown file"""
        try:
            # Create plans directory if it doesn't exist
            plans_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"plan_{task_id}_{timestamp}.md"
            filepath = plans_dir / filename

            # Save plan
            filepath.write_text(plan, encoding="utf-8")
            logger.info(f"Plan saved to {filepath}")

            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save plan: {e}")
            raise Exception(f"Plan save failed: {str(e)}")

    async def generate_report(
        self,
        task_description: str,
        plan: str,
        implementation_summary: str,
        test_results: dict,
        commit_hash: str,
        branch_name: str,
    ) -> str:
        """Generate a completion report"""
        try:
            logger.info("Generating completion report")

            prompt = f"""Generate a comprehensive completion report for the following task.

## TASK
{task_description}

## IMPLEMENTATION SUMMARY
{implementation_summary}

## TEST RESULTS
- Tests Passed: {test_results.get('passed', 0)}
- Tests Failed: {test_results.get('failed', 0)}
- Total Tests: {test_results.get('total', 0)}
- Test Output: {test_results.get('output', 'No output')}

## GIT INFORMATION
- Branch: {branch_name}
- Commit Hash: {commit_hash}

## YOUR TASK
Create a detailed completion report in Markdown format that includes:

1. **Task Summary**: Brief recap of what was requested
2. **Implementation Details**: What was actually implemented
3. **Changes Made**: Files created/modified with brief descriptions
4. **Test Results**: Summary of test execution and results
5. **How to Use**: Instructions for using/testing the new feature
6. **Git Information**: Branch name and commit hash for review
7. **Next Steps**: Suggested follow-up tasks or improvements (if any)
8. **Known Issues**: Any issues or limitations (if any)

Generate the report now:
"""

            response = await self.llm.ainvoke(prompt)
            report = response.content

            logger.info("Completion report generated successfully")
            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise Exception(f"Report generation failed: {str(e)}")

    async def save_report(self, report: str, task_id: str, reports_dir: Path) -> str:
        """Save the completion report to a markdown file"""
        try:
            # Create reports directory if it doesn't exist
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{task_id}_{timestamp}.md"
            filepath = reports_dir / filename

            # Save report
            filepath.write_text(report, encoding="utf-8")
            logger.info(f"Report saved to {filepath}")

            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise Exception(f"Report save failed: {str(e)}")
