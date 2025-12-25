from langchain_openai import ChatOpenAI
from pathlib import Path
from typing import Dict, List
from loguru import logger
import os
import re


class DeveloperAgent:
    """Agent responsible for implementing code based on plans"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def implement(
        self, plan: str, project_context: dict, repository_path: Path
    ) -> Dict:
        """Implement the feature based on the plan"""
        try:
            logger.info("Starting code implementation")

            # Parse the plan to extract file operations
            file_operations = await self._parse_plan(plan)

            files_modified = []
            files_created = []
            implementation_log = []

            # Create new files
            for file_info in file_operations.get("files_to_create", []):
                try:
                    filepath = repository_path / file_info["path"]
                    logger.info(f"Creating file: {file_info['path']}")

                    # Generate code for the file
                    code = await self._generate_code_for_file(
                        file_path=file_info["path"],
                        purpose=file_info.get("purpose", ""),
                        plan=plan,
                        project_context=project_context,
                        repository_path=repository_path,
                    )

                    # Ensure parent directory exists
                    filepath.parent.mkdir(parents=True, exist_ok=True)

                    # Write the file
                    filepath.write_text(code, encoding="utf-8")
                    files_created.append(file_info["path"])
                    implementation_log.append(f"✓ Created: {file_info['path']}")
                    logger.info(f"Successfully created: {file_info['path']}")

                except Exception as e:
                    error_msg = f"✗ Failed to create {file_info['path']}: {str(e)}"
                    implementation_log.append(error_msg)
                    logger.error(error_msg)

            # Modify existing files
            for file_info in file_operations.get("files_to_modify", []):
                try:
                    filepath = repository_path / file_info["path"]
                    logger.info(f"Modifying file: {file_info['path']}")

                    if not filepath.exists():
                        logger.warning(
                            f"File does not exist, will create: {file_info['path']}"
                        )
                        # Treat as new file
                        code = await self._generate_code_for_file(
                            file_path=file_info["path"],
                            purpose=file_info.get("changes", ""),
                            plan=plan,
                            project_context=project_context,
                            repository_path=repository_path,
                        )
                        filepath.parent.mkdir(parents=True, exist_ok=True)
                        filepath.write_text(code, encoding="utf-8")
                        files_created.append(file_info["path"])
                    else:
                        # Read existing content
                        existing_code = filepath.read_text(encoding="utf-8")

                        # Generate modifications
                        modified_code = await self._modify_existing_file(
                            file_path=file_info["path"],
                            existing_code=existing_code,
                            changes_needed=file_info.get("changes", ""),
                            plan=plan,
                            project_context=project_context,
                        )

                        # Write modified content
                        filepath.write_text(modified_code, encoding="utf-8")
                        files_modified.append(file_info["path"])

                    implementation_log.append(f"✓ Modified: {file_info['path']}")
                    logger.info(f"Successfully modified: {file_info['path']}")

                except Exception as e:
                    error_msg = f"✗ Failed to modify {file_info['path']}: {str(e)}"
                    implementation_log.append(error_msg)
                    logger.error(error_msg)

            # Generate implementation summary
            summary = "\n".join(implementation_log)

            logger.info(
                f"Implementation completed: {len(files_created)} created, {len(files_modified)} modified"
            )

            return {
                "files_created": files_created,
                "files_modified": files_modified,
                "summary": summary,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Implementation failed: {e}")
            raise Exception(f"Implementation failed: {str(e)}")

    async def _parse_plan(self, plan: str) -> Dict:
        """Parse the plan to extract file operations"""
        try:
            logger.info("Parsing implementation plan")

            prompt = f"""Parse the following implementation plan and extract file operations.

PLAN:
{plan}

Extract and return ONLY a JSON object with this structure:
{{
    "files_to_create": [
        {{"path": "relative/path/to/file.py", "purpose": "brief purpose"}}
    ],
    "files_to_modify": [
        {{"path": "relative/path/to/file.py", "changes": "what needs to change"}}
    ]
}}

Return ONLY valid JSON, nothing else. If no files found, return empty arrays.
"""

            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()

            # Extract JSON from potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Parse JSON
            import json

            file_operations = json.loads(content)

            logger.info(
                f"Parsed plan: {len(file_operations.get('files_to_create', []))} to create, "
                f"{len(file_operations.get('files_to_modify', []))} to modify"
            )

            return file_operations

        except Exception as e:
            logger.error(f"Failed to parse plan: {e}")
            # Return empty structure on error
            return {"files_to_create": [], "files_to_modify": []}

    async def _generate_code_for_file(
        self,
        file_path: str,
        purpose: str,
        plan: str,
        project_context: dict,
        repository_path: Path,
    ) -> str:
        """Generate code for a new file"""
        try:
            logger.info(f"Generating code for: {file_path}")

            # Get context from similar files if they exist
            context_code = await self._get_context_from_repo(file_path, repository_path)

            prompt = f"""You are an expert software developer. Generate complete, production-ready code for a new file.

FILE PATH: {file_path}
PURPOSE: {purpose}

PROJECT CONTEXT:
- Tech Stack: {project_context.get('tech_stack', 'Python')}
- Coding Style: {project_context.get('coding_style', 'PEP 8')}
- Test Framework: {project_context.get('test_framework', 'pytest')}

IMPLEMENTATION PLAN EXCERPT:
{plan[:1500]}

SIMILAR FILES IN REPO (for reference):
{context_code[:1000] if context_code else 'No similar files found'}

REQUIREMENTS:
1. Write complete, working code (no TODOs or placeholders)
2. Include all necessary imports
3. Add proper error handling
4. Include docstrings for functions/classes
5. Follow the project's coding style
6. Make the code production-ready
7. Add type hints where appropriate

Generate ONLY the code content for {file_path}, no explanations or markdown:
"""

            response = await self.llm.ainvoke(prompt)
            code = response.content.strip()

            # Remove markdown code blocks if present
            if code.startswith("```"):
                lines = code.split("\n")
                # Remove first line (```python or similar)
                lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                code = "\n".join(lines)

            logger.info(f"Generated {len(code)} characters of code for {file_path}")
            return code

        except Exception as e:
            logger.error(f"Failed to generate code for {file_path}: {e}")
            raise

    async def _modify_existing_file(
        self,
        file_path: str,
        existing_code: str,
        changes_needed: str,
        plan: str,
        project_context: dict,
    ) -> str:
        """Modify an existing file"""
        try:
            logger.info(f"Modifying existing file: {file_path}")

            prompt = f"""You are an expert software developer. Modify the existing code according to the requirements.

FILE PATH: {file_path}
CHANGES NEEDED: {changes_needed}

EXISTING CODE:
```
{existing_code}
```

PROJECT CONTEXT:
- Tech Stack: {project_context.get('tech_stack', 'Python')}
- Coding Style: {project_context.get('coding_style', 'PEP 8')}

IMPLEMENTATION PLAN EXCERPT:
{plan[:1500]}

REQUIREMENTS:
1. Preserve existing functionality unless it needs to change
2. Add requested features/modifications
3. Maintain code style consistency
4. Update imports if needed
5. Add proper error handling for new code
6. Keep or improve existing docstrings
7. Ensure the code is complete and working

Generate the COMPLETE modified file content (not just the changes), no explanations or markdown:
"""

            response = await self.llm.ainvoke(prompt)
            modified_code = response.content.strip()

            # Remove markdown code blocks if present
            if modified_code.startswith("```"):
                lines = modified_code.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                modified_code = "\n".join(lines)

            logger.info(f"Modified file {file_path}: {len(modified_code)} characters")
            return modified_code

        except Exception as e:
            logger.error(f"Failed to modify {file_path}: {e}")
            raise

    async def _get_context_from_repo(
        self, file_path: str, repository_path: Path
    ) -> str:
        """Get code from similar files for context"""
        try:
            # Determine file type
            file_extension = Path(file_path).suffix

            # Look for similar files
            similar_files = []
            for root, dirs, files in os.walk(repository_path):
                # Skip common ignore patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "__pycache__", "venv"]
                ]

                for file in files:
                    if file.endswith(file_extension) and not file.startswith("."):
                        file_full_path = Path(root) / file
                        # Don't include files that are too large
                        if file_full_path.stat().st_size < 50000:  # 50KB limit
                            similar_files.append(file_full_path)

                # Limit to first 3 files
                if len(similar_files) >= 3:
                    break

            # Read content from similar files
            context = []
            for similar_file in similar_files[:3]:
                try:
                    content = similar_file.read_text(encoding="utf-8")
                    relative_path = similar_file.relative_to(repository_path)
                    context.append(f"# File: {relative_path}\n{content[:500]}\n")
                except:
                    continue

            return "\n".join(context)

        except Exception as e:
            logger.warning(f"Could not get context from repo: {e}")
            return ""
