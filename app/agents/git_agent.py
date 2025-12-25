import git
import os
from pathlib import Path
from typing import Optional, List
from loguru import logger
from app.config import settings
import re


class GitAgent:
    """Agent responsible for all Git operations"""

    def __init__(self):
        self.user_name = settings.GIT_USER_NAME
        self.user_email = settings.GIT_USER_EMAIL
        self.main_branch_names = settings.MAIN_BRANCH_NAMES

    async def clone_repository(self, repo_url: str, local_path: Path) -> git.Repo:
        """Clone a repository to local path"""
        try:
            logger.info(f"Cloning repository: {repo_url} to {local_path}")

            # Create parent directory if it doesn't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Clone the repository
            repo = git.Repo.clone_from(repo_url, local_path)

            # Configure git user
            with repo.config_writer() as config:
                config.set_value("user", "name", self.user_name)
                config.set_value("user", "email", self.user_email)

            logger.info(f"Repository cloned successfully to {local_path}")
            return repo

        except git.GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise Exception(f"Git clone failed: {str(e)}")

    async def detect_main_branch(self, repo_path: Path) -> str:
        """Detect the main branch name (main, dev, development, master)"""
        try:
            repo = git.Repo(repo_path)

            # Get all remote branches
            remote_branches = [ref.name.split("/")[-1] for ref in repo.remote().refs]

            # Check for common main branch names
            for branch_name in self.main_branch_names:
                if branch_name in remote_branches:
                    logger.info(f"Detected main branch: {branch_name}")
                    return branch_name

            # Default to first branch if none found
            default_branch = remote_branches[0] if remote_branches else "main"
            logger.warning(f"No standard main branch found, using: {default_branch}")
            return default_branch

        except Exception as e:
            logger.error(f"Failed to detect main branch: {e}")
            raise Exception(f"Branch detection failed: {str(e)}")

    async def pull_latest(self, repo_path: Path, branch: str) -> None:
        """Pull latest changes from remote branch"""
        try:
            repo = git.Repo(repo_path)
            origin = repo.remote("origin")

            # Checkout the branch
            if branch not in [b.name for b in repo.branches]:
                # Create local branch tracking remote
                repo.git.checkout("-b", branch, f"origin/{branch}")
            else:
                repo.git.checkout(branch)

            # Pull latest changes
            logger.info(f"Pulling latest changes from {branch}")
            origin.pull(branch)
            logger.info(f"Successfully pulled latest changes from {branch}")

        except git.GitCommandError as e:
            logger.error(f"Failed to pull latest changes: {e}")
            raise Exception(f"Git pull failed: {str(e)}")

    async def create_branch(self, repo_path: Path, branch_name: str) -> None:
        """Create and checkout a new branch"""
        try:
            repo = git.Repo(repo_path)

            # Check if branch already exists
            if branch_name in [b.name for b in repo.branches]:
                logger.warning(f"Branch {branch_name} already exists, checking it out")
                repo.git.checkout(branch_name)
            else:
                # Create new branch
                logger.info(f"Creating new branch: {branch_name}")
                repo.git.checkout("-b", branch_name)
                logger.info(
                    f"Successfully created and checked out branch: {branch_name}"
                )

        except git.GitCommandError as e:
            logger.error(f"Failed to create branch: {e}")
            raise Exception(f"Branch creation failed: {str(e)}")

    async def generate_branch_name(self, task_description: str) -> str:
        """Generate a branch name from task description"""
        # Convert to lowercase and replace spaces with hyphens
        branch_name = task_description.lower()

        # Remove special characters
        branch_name = re.sub(r"[^a-z0-9\s-]", "", branch_name)

        # Replace spaces with hyphens
        branch_name = re.sub(r"\s+", "-", branch_name)

        # Limit length
        branch_name = branch_name[:50]

        # Add feature prefix
        branch_name = f"feature/{branch_name}"

        logger.info(f"Generated branch name: {branch_name}")
        return branch_name

    async def commit_and_push(
        self, repo_path: Path, branch_name: str, commit_message: str
    ) -> str:
        """Commit changes and push to remote"""
        try:
            repo = git.Repo(repo_path)

            # Add all changes
            logger.info("Adding all changes to git")
            repo.git.add(A=True)

            # Check if there are changes to commit
            if not repo.is_dirty() and not repo.untracked_files:
                logger.warning("No changes to commit")
                return ""

            # Commit changes
            logger.info(f"Committing changes: {commit_message[:50]}...")
            commit = repo.index.commit(commit_message)
            commit_hash = commit.hexsha

            # Push to remote
            logger.info(f"Pushing branch {branch_name} to remote")
            origin = repo.remote("origin")
            origin.push(branch_name)

            logger.info(
                f"Successfully pushed commit {commit_hash[:8]} to {branch_name}"
            )
            return commit_hash

        except git.GitCommandError as e:
            logger.error(f"Failed to commit and push: {e}")
            raise Exception(f"Git commit/push failed: {str(e)}")

    async def generate_commit_message(
        self, task_description: str, files_modified: List[str], files_created: List[str]
    ) -> str:
        """Generate a descriptive commit message"""
        # Create commit message
        message_lines = [
            f"feat: {task_description[:72]}",
            "",
            "Changes made by AI Coding Assistant:",
            "",
        ]

        if files_created:
            message_lines.append("Created files:")
            for file in files_created[:5]:  # Limit to first 5
                message_lines.append(f"  - {file}")
            if len(files_created) > 5:
                message_lines.append(f"  ... and {len(files_created) - 5} more")
            message_lines.append("")

        if files_modified:
            message_lines.append("Modified files:")
            for file in files_modified[:5]:  # Limit to first 5
                message_lines.append(f"  - {file}")
            if len(files_modified) > 5:
                message_lines.append(f"  ... and {len(files_modified) - 5} more")

        commit_message = "\n".join(message_lines)
        logger.info(f"Generated commit message: {commit_message[:100]}...")
        return commit_message

    async def get_repository_info(self, repo_path: Path) -> dict:
        """Get repository information"""
        try:
            repo = git.Repo(repo_path)

            return {
                "current_branch": repo.active_branch.name,
                "remote_url": repo.remote().url,
                "latest_commit": repo.head.commit.hexsha,
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
            }

        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            return {}

    async def rollback_branch(self, repo_path: Path, branch_name: str) -> None:
        """Delete a branch (rollback on failure)"""
        try:
            repo = git.Repo(repo_path)

            # Checkout main branch first
            main_branch = await self.detect_main_branch(repo_path)
            repo.git.checkout(main_branch)

            # Delete the branch
            logger.info(f"Rolling back branch: {branch_name}")
            repo.git.branch("-D", branch_name)
            logger.info(f"Successfully deleted branch: {branch_name}")

        except git.GitCommandError as e:
            logger.error(f"Failed to rollback branch: {e}")
            # Don't raise - rollback is best-effort
