"""
GitHub-related commands.
"""
from typing import List, Dict, Any
from ..base import Command, CommandResult
from utils.logger import get_logger

logger = get_logger(__name__)


class CreatePRCommand(Command):
    """Create a GitHub pull request."""
    
    def __init__(self, github_monitor):
        """Initialize command.
        
        Args:
            github_monitor: GitHubMonitor instance
        """
        self.github = github_monitor
    
    @property
    def name(self) -> str:
        return "create-pr"
    
    @property
    def description(self) -> str:
        return "Create a pull request"
    
    @property
    def usage(self) -> str:
        return "agent create-pr <branch> [to <base>] [--title \"PR Title\"]"
    
    @property
    def aliases(self) -> List[str]:
        return ["pr", "new-pr"]
    
    @property
    def category(self) -> str:
        return "GitHub"
    
    def validate_args(self, args: List[str]) -> bool:
        """Validate arguments."""
        return len(args) >= 1
    
    async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """Execute command."""
        # Parse arguments
        branch = args[0]
        base = "main"
        title = None
        
        # Check for "to <base>"
        i = 1
        while i < len(args):
            if args[i].lower() == "to" and i + 1 < len(args):
                base = args[i + 1]
                i += 2
            elif args[i] == "--title" and i + 1 < len(args):
                title = args[i + 1]
                i += 2
            else:
                i += 1
        
        # Get repository from context
        repo = context.get('default_repo')
        if not repo:
            return CommandResult(
                success=False,
                message="No default repository configured",
                error="Add 'repos' to your GitHub configuration"
            )
        
        try:
            # Create PR
            if not title:
                title = f"Merge {branch} into {base}"
            
            pr = self.github.create_pr(
                repo_name=repo,
                title=title,
                body=f"Created via agent command\n\nBranch: `{branch}` → `{base}`",
                head=branch,
                base=base
            )
            
            if pr:
                return CommandResult(
                    success=True,
                    message=f"Created PR #{pr.number}: {pr.title}",
                    data={
                        "pr_number": pr.number,
                        "url": pr.html_url,
                        "title": pr.title
                    }
                )
            else:
                return CommandResult(
                    success=False,
                    message="Failed to create PR",
                    error="Check logs for details"
                )
        
        except Exception as e:
            logger.error(f"Failed to create PR: {e}", exc_info=True)
            return CommandResult(
                success=False,
                message="Failed to create PR",
                error=str(e)
            )


class MergePRCommand(Command):
    """Merge a GitHub pull request."""
    
    def __init__(self, github_monitor):
        """Initialize command.
        
        Args:
            github_monitor: GitHubMonitor instance
        """
        self.github = github_monitor
    
    @property
    def name(self) -> str:
        return "merge-pr"
    
    @property
    def description(self) -> str:
        return "Merge a pull request"
    
    @property
    def usage(self) -> str:
        return "agent merge-pr <pr_number> [--method squash|merge|rebase]"
    
    @property
    def aliases(self) -> List[str]:
        return ["merge"]
    
    @property
    def category(self) -> str:
        return "GitHub"
    
    def validate_args(self, args: List[str]) -> bool:
        """Validate arguments."""
        if len(args) < 1:
            return False
        
        # Check if first arg is a number (with or without #)
        pr_str = args[0].lstrip('#')
        return pr_str.isdigit()
    
    async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """Execute command."""
        # Parse PR number
        pr_number = int(args[0].lstrip('#'))
        
        # Parse merge method
        merge_method = "squash"  # default
        i = 1
        while i < len(args):
            if args[i] == "--method" and i + 1 < len(args):
                method = args[i + 1].lower()
                if method in ["squash", "merge", "rebase"]:
                    merge_method = method
                i += 2
            else:
                i += 1
        
        # Get repository from context
        repo = context.get('default_repo')
        if not repo:
            return CommandResult(
                success=False,
                message="No default repository configured",
                error="Add 'repos' to your GitHub configuration"
            )
        
        try:
            # Merge PR
            success = self.github.merge_pr(repo, pr_number, merge_method)
            
            if success:
                return CommandResult(
                    success=True,
                    message=f"Merged PR #{pr_number} using {merge_method} method",
                    data={"pr_number": pr_number, "method": merge_method}
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Failed to merge PR #{pr_number}",
                    error="PR may have failing checks or conflicts"
                )
        
        except Exception as e:
            logger.error(f"Failed to merge PR: {e}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Failed to merge PR #{pr_number}",
                error=str(e)
            )


class CheckPRsCommand(Command):
    """Check open pull requests."""
    
    def __init__(self, github_monitor):
        """Initialize command.
        
        Args:
            github_monitor: GitHubMonitor instance
        """
        self.github = github_monitor
    
    @property
    def name(self) -> str:
        return "check-prs"
    
    @property
    def description(self) -> str:
        return "List open pull requests"
    
    @property
    def usage(self) -> str:
        return "agent check-prs [repo]"
    
    @property
    def aliases(self) -> List[str]:
        return ["list-prs", "prs"]
    
    @property
    def category(self) -> str:
        return "GitHub"
    
    async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """Execute command."""
        # Get repository
        if args:
            repo = args[0]
        else:
            repo = context.get('default_repo')
        
        if not repo:
            return CommandResult(
                success=False,
                message="No repository specified",
                error="Usage: agent check-prs [repo]"
            )
        
        try:
            # Get open PRs
            prs = self.github.get_open_prs(repo)
            
            if not prs:
                return CommandResult(
                    success=True,
                    message=f"No open PRs in {repo}",
                    data={"count": 0}
                )
            
            # Format PR list
            pr_list = f"**Open PRs in {repo}** ({len(prs)} total):\n\n"
            for pr in prs[:10]:  # Limit to 10
                pr_list += f"• #{pr.number}: {pr.title}\n"
                pr_list += f"  Author: {pr.user.login} | "
                pr_list += f"Created: {pr.created_at.strftime('%Y-%m-%d')}\n"
            
            if len(prs) > 10:
                pr_list += f"\n... and {len(prs) - 10} more"
            
            return CommandResult(
                success=True,
                message=pr_list,
                data={"count": len(prs)}
            )
        
        except Exception as e:
            logger.error(f"Failed to check PRs: {e}", exc_info=True)
            return CommandResult(
                success=False,
                message="Failed to check PRs",
                error=str(e)
            )


class CommentPRCommand(Command):
    """Add a comment to a pull request."""
    
    def __init__(self, github_monitor):
        """Initialize command.
        
        Args:
            github_monitor: GitHubMonitor instance
        """
        self.github = github_monitor
    
    @property
    def name(self) -> str:
        return "comment-pr"
    
    @property
    def description(self) -> str:
        return "Add a comment to a pull request"
    
    @property
    def usage(self) -> str:
        return "agent comment-pr <pr_number> <comment>"
    
    @property
    def aliases(self) -> List[str]:
        return ["comment"]
    
    @property
    def category(self) -> str:
        return "GitHub"
    
    def validate_args(self, args: List[str]) -> bool:
        """Validate arguments."""
        if len(args) < 2:
            return False
        
        # Check if first arg is a number
        pr_str = args[0].lstrip('#')
        return pr_str.isdigit()
    
    async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """Execute command."""
        # Parse arguments
        pr_number = int(args[0].lstrip('#'))
        comment = ' '.join(args[1:])
        
        # Get repository from context
        repo = context.get('default_repo')
        if not repo:
            return CommandResult(
                success=False,
                message="No default repository configured",
                error="Add 'repos' to your GitHub configuration"
            )
        
        try:
            # Add comment
            success = self.github.add_comment_to_pr(repo, pr_number, comment)
            
            if success:
                return CommandResult(
                    success=True,
                    message=f"Added comment to PR #{pr_number}",
                    data={"pr_number": pr_number}
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Failed to comment on PR #{pr_number}",
                    error="Check logs for details"
                )
        
        except Exception as e:
            logger.error(f"Failed to comment on PR: {e}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Failed to comment on PR #{pr_number}",
                error=str(e)
            )
