"""
GitHub integration for monitoring PRs and managing repositories.
"""
import os
import time
import threading
from typing import Dict, Any, List
from github import Github, GithubException
from integrations.base_monitor import BaseMonitor
from utils.logger import get_logger

logger = get_logger(__name__)


class GitHubMonitor(BaseMonitor):
    """Monitor GitHub for PR events and repository changes."""
    
    def __init__(self):
        super().__init__("GitHubMonitor")
        self.gh = None
        self.repos = []
        self.poll_interval = 60  # seconds
        self.thread = None
        self.last_check = {}
    
    def start(self, config: Dict[str, Any]):
        """
        Start GitHub monitoring.
        
        Args:
            config: GitHub configuration with 'token' and 'repos'
        """
        if self.running:
            logger.warning("GitHub monitor already running")
            return
        
        self.config = config
        token = config.get('token') or os.getenv('GITHUB_TOKEN')
        
        if not token:
            logger.error("GitHub token not configured")
            return
        
        try:
            self.gh = Github(token)
            self.repos = config.get('repos', [])
            self.poll_interval = config.get('poll_interval', 60)
            
            # Start monitoring thread
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"GitHub monitor started for {len(self.repos)} repos")
        
        except Exception as e:
            logger.error(f"Failed to start GitHub monitor: {e}", exc_info=True)
            self.running = False
    
    def stop(self):
        """Stop GitHub monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("GitHub monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                for repo_name in self.repos:
                    self._check_repo(repo_name)
                
                time.sleep(self.poll_interval)
            
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)
    
    def _check_repo(self, repo_name: str):
        """
        Check repository for events.
        
        Args:
            repo_name: Repository name (owner/repo)
        """
        try:
            repo = self.gh.get_repo(repo_name)
            
            # Check PRs
            prs = repo.get_pulls(state='open')
            
            for pr in prs:
                pr_key = f"{repo_name}#{pr.number}"
                
                # Check if PR is ready to merge
                if self._is_ready_to_merge(pr):
                    self.trigger_callbacks("pr_ready_to_merge", {
                        "repo": repo_name,
                        "pr": pr,
                        "number": pr.number,
                        "title": pr.title
                    })
                
                # Check if PR needs review
                elif self._needs_review(pr):
                    # Only trigger if we haven't seen this before
                    if pr_key not in self.last_check:
                        self.trigger_callbacks("pr_needs_review", {
                            "repo": repo_name,
                            "pr": pr,
                            "number": pr.number,
                            "title": pr.title
                        })
                
                self.last_check[pr_key] = time.time()
        
        except GithubException as e:
            logger.error(f"GitHub API error for {repo_name}: {e}")
        except Exception as e:
            logger.error(f"Error checking {repo_name}: {e}", exc_info=True)
    
    def _is_ready_to_merge(self, pr) -> bool:
        """
        Check if PR is ready to merge.
        
        Args:
            pr: Pull request object
        
        Returns:
            bool: True if ready to merge
        """
        if not pr.mergeable:
            return False
        
        # Check reviews
        reviews = list(pr.get_reviews())
        approved_count = sum(1 for r in reviews if r.state == 'APPROVED')
        
        min_approvals = self.config.get('min_approvals', 1)
        if approved_count < min_approvals:
            return False
        
        # Check CI status
        if self.config.get('require_ci_pass', True):
            commit = pr.get_commits().reversed[0]
            statuses = commit.get_combined_status()
            if statuses.state != 'success':
                return False
        
        return True
    
    def _needs_review(self, pr) -> bool:
        """
        Check if PR needs review.
        
        Args:
            pr: Pull request object
        
        Returns:
            bool: True if needs review
        """
        reviews = list(pr.get_reviews())
        return len(reviews) == 0
    
    def merge_pr(self, repo_name: str, pr_number: int, merge_method: str = "merge"):
        """
        Merge a pull request.
        
        Args:
            repo_name: Repository name
            pr_number: PR number
            merge_method: Merge method ('merge', 'squash', 'rebase')
        
        Returns:
            bool: True if merged successfully
        """
        try:
            repo = self.gh.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            result = pr.merge(merge_method=merge_method)
            
            if result.merged:
                logger.info(f"Merged PR #{pr_number} in {repo_name}")
                return True
            else:
                logger.warning(f"Failed to merge PR #{pr_number}: {result.message}")
                return False
        
        except Exception as e:
            logger.error(f"Error merging PR #{pr_number}: {e}", exc_info=True)
            return False
    
    def create_pr(self, repo_name: str, title: str, body: str, head: str, base: str = "main"):
        """
        Create a new pull request.
        
        Args:
            repo_name: Repository name
            title: PR title
            body: PR description
            head: Head branch
            base: Base branch
        
        Returns:
            Pull request object or None
        """
        try:
            repo = self.gh.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            logger.info(f"Created PR #{pr.number} in {repo_name}")
            return pr
        except Exception as e:
            logger.error(f"Error creating PR: {e}", exc_info=True)
            return None
    
    def get_open_prs(self, repo_name: str) -> List:
        """
        Get all open PRs for a repository.
        
        Args:
            repo_name: Repository name
        
        Returns:
            List of PR objects
        """
        try:
            repo = self.gh.get_repo(repo_name)
            return list(repo.get_pulls(state='open'))
        except Exception as e:
            logger.error(f"Error getting PRs: {e}", exc_info=True)
            return []
