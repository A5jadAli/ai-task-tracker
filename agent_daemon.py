#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Production Agent Daemon - Long-running automation system.

This daemon integrates:
- Event monitoring (Slack, GitHub)
- Task scheduling (cron-style)
- Workflow execution
- Background task processing
"""
import os
import sys
import signal
import time
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger, get_logger
from utils.config_parser import load_config
from utils.task_queue import TaskQueue
from utils.rate_limiter import MultiProviderRateLimiter
from agent.scheduler import TaskScheduler
from agent.event_dispatcher import EventDispatcher
from agent.core import AutonomousAgent
from integrations.slack_monitor import SlackMonitor
from integrations.github_monitor import GitHubMonitor

# Setup logging
logger = setup_logger('agent_daemon', 'logs/agent.log')


class AgentDaemon:
    """Main daemon process for the production agent."""
    
    def __init__(self, config_path: str):
        """
        Initialize daemon.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = None
        self.running = False
        
        # Components
        self.task_queue = None
        self.scheduler = None
        self.dispatcher = None
        self.agent = None
        self.monitors = {}
        self.rate_limiter = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start the daemon."""
        if self.running:
            logger.warning("Daemon already running")
            return
        
        logger.info("=" * 60)
        logger.info("Starting Production Agent Daemon")
        logger.info("=" * 60)
        
        try:
            # Load configuration
            logger.info(f"Loading configuration from: {self.config_path}")
            self.config = load_config(self.config_path)
            
            # Initialize components
            self._initialize_components()
            
            # Start monitors
            self._start_monitors()
            
            # Setup scheduled tasks
            self._setup_scheduled_tasks()
            
            # Setup workflows
            self._setup_workflows()
            
            self.running = True
            logger.info("✓ Daemon started successfully")
            logger.info("=" * 60)
            
            # Main loop
            self._main_loop()
        
        except Exception as e:
            logger.error(f"Failed to start daemon: {e}", exc_info=True)
            self.stop()
            sys.exit(1)
    
    def _initialize_components(self):
        """Initialize all daemon components."""
        logger.info("Initializing components...")
        
        # Task queue
        queue_config = self.config.get('task_queue', {})
        num_workers = queue_config.get('num_workers', 3)
        self.task_queue = TaskQueue(num_workers=num_workers)
        self.task_queue.start()
        logger.info(f"✓ Task queue started with {num_workers} workers")
        
        # Scheduler
        self.scheduler = TaskScheduler()
        self.scheduler.start()
        logger.info("✓ Scheduler started")
        
        # Event dispatcher
        self.dispatcher = EventDispatcher()
        logger.info("✓ Event dispatcher initialized")
        
        # Rate limiter
        self.rate_limiter = MultiProviderRateLimiter()
        ai_config = self.config.get('ai', {})
        rate_limit = ai_config.get('rate_limit_per_minute', 15)
        self.rate_limiter.add_provider('gemini', rate_limit, 60)
        self.rate_limiter.add_provider('openai', 60, 60)
        logger.info("✓ Rate limiter configured")
        
        # Agent
        self.agent = AutonomousAgent()
        logger.info("✓ Agent initialized")
    
    def _start_monitors(self):
        """Start all configured monitors."""
        logger.info("Starting monitors...")
        
        monitoring_config = self.config.get('monitoring', {})
        
        # Slack monitor
        slack_config = monitoring_config.get('slack', {})
        if slack_config.get('enabled', False):
            try:
                slack_monitor = SlackMonitor()
                
                # Register callbacks for both bot and user modes
                slack_monitor.register_callback('mention', self._handle_slack_mention)
                slack_monitor.register_callback('user_mention', self._handle_slack_user_mention)
                slack_monitor.register_callback('dm_received', self._handle_slack_dm)
                slack_monitor.register_callback('keyword', self._handle_slack_keyword)
                
                slack_monitor.start(slack_config)
                self.monitors['slack'] = slack_monitor
                logger.info("✓ Slack monitor started")
            except Exception as e:
                logger.error(f"Failed to start Slack monitor: {e}")
        
        # GitHub monitor
        github_config = monitoring_config.get('github', {})
        if github_config.get('enabled', False):
            try:
                github_monitor = GitHubMonitor()
                
                # Register callbacks for both bot and user modes
                github_monitor.register_callback('pr_ready_to_merge', self._handle_pr_ready)
                github_monitor.register_callback('pr_needs_review', self._handle_pr_review)
                github_monitor.register_callback('user_mentioned_in_pr', self._handle_user_mentioned_in_pr)
                github_monitor.register_callback('user_assigned_to_pr', self._handle_user_assigned_to_pr)
                github_monitor.register_callback('user_notification', self._handle_user_notification)
                
                github_monitor.start(github_config)
                self.monitors['github'] = github_monitor
                logger.info("✓ GitHub monitor started")
            except Exception as e:
                logger.error(f"Failed to start GitHub monitor: {e}")
    
    def _setup_scheduled_tasks(self):
        """Setup scheduled tasks from configuration."""
        logger.info("Setting up scheduled tasks...")
        
        scheduled_tasks = self.config.get('scheduled_tasks', [])
        
        for task_config in scheduled_tasks:
            task_name = task_config.get('name')
            schedule = task_config.get('schedule')
            workflow = task_config.get('workflow')
            
            if not all([task_name, schedule, workflow]):
                logger.warning(f"Invalid task configuration: {task_config}")
                continue
            
            # Create task function
            def task_func(workflow_name=workflow):
                logger.info(f"Executing scheduled task: {workflow_name}")
                self._execute_workflow(workflow_name, {})
            
            # Add to scheduler
            self.scheduler.add_cron_task(task_name, task_func, schedule)
            logger.info(f"✓ Scheduled task '{task_name}': {schedule}")
    
    def _setup_workflows(self):
        """Setup workflows from configuration."""
        logger.info("Setting up workflows...")
        
        workflows = self.config.get('workflows', {})
        logger.info(f"✓ Loaded {len(workflows)} workflows")
    
    def _execute_workflow(self, workflow_name: str, context: dict):
        """
        Execute a workflow.
        
        Args:
            workflow_name: Name of workflow to execute
            context: Workflow context data
        """
        workflows = self.config.get('workflows', {})
        
        if workflow_name not in workflows:
            logger.error(f"Workflow '{workflow_name}' not found")
            return
        
        workflow = workflows[workflow_name]
        steps = workflow.get('steps', [])
        
        logger.info(f"Executing workflow '{workflow_name}' with {len(steps)} steps")
        
        for i, step in enumerate(steps):
            step_type = step.get('type')
            action = step.get('action')
            params = step.get('params', {})
            
            logger.info(f"Step {i+1}/{len(steps)}: {step_type}.{action}")
            
            try:
                if step_type == 'slack':
                    self._execute_slack_action(action, params, context)
                elif step_type == 'github':
                    self._execute_github_action(action, params, context)
                elif step_type == 'ai':
                    self._execute_ai_action(action, params, context)
                elif step_type == 'log':
                    message = params.get('message', '').format(**context)
                    logger.info(f"Workflow log: {message}")
                else:
                    logger.warning(f"Unknown step type: {step_type}")
            
            except Exception as e:
                logger.error(f"Error in workflow step: {e}", exc_info=True)
    
    def _execute_slack_action(self, action: str, params: dict, context: dict):
        """Execute Slack action."""
        if 'slack' not in self.monitors:
            logger.error("Slack monitor not available")
            return
        
        slack = self.monitors['slack']
        
        if action == 'send_message':
            channel = params.get('channel')
            message = params.get('message', '').format(**context)
            slack.send_message(channel, message)
        elif action == 'send_reply':
            channel = context.get('event', {}).get('channel')
            thread_ts = context.get('event', {}).get('ts')
            message = params.get('message', '').format(**context)
            slack.reply_to_thread(channel, thread_ts, message)
    
    def _execute_github_action(self, action: str, params: dict, context: dict):
        """Execute GitHub action."""
        if 'github' not in self.monitors:
            logger.error("GitHub monitor not available")
            return
        
        github = self.monitors['github']
        
        if action == 'merge_pr':
            repo = context.get('repo')
            pr_number = context.get('number')
            merge_method = params.get('merge_method', 'merge')
            github.merge_pr(repo, pr_number, merge_method)
        elif action == 'add_comment':
            repo = context.get('repo')
            pr_number = context.get('number')
            comment = params.get('comment', context.get('ai_response', ''))
            github.add_comment_to_pr(repo, pr_number, comment)
        elif action == 'check_all_prs':
            # This is handled by the monitor's polling
            pass
    
    def _execute_ai_action(self, action: str, params: dict, context: dict):
        """Execute AI action."""
        objective = params.get('objective', '')
        
        # Use rate limiter
        self.rate_limiter.wait_if_needed('gemini')
        
        # Execute AI task
        result = self.agent.brain.think_about_task(objective)
        context['ai_response'] = result.get('content', '')
    
    def _handle_slack_mention(self, event: dict):
        """Handle Slack mention events."""
        logger.info("Handling Slack mention")
        self.dispatcher.dispatch('slack_mention', event)
        
        # Execute configured workflow
        monitoring_config = self.config.get('monitoring', {})
        slack_actions = monitoring_config.get('slack', {}).get('actions', [])
        
        for action_config in slack_actions:
            if action_config.get('trigger') == 'mention':
                workflow = action_config.get('workflow')
                if workflow:
                    self.task_queue.add_task(
                        self._execute_workflow,
                        workflow,
                        {'event': event}
                    )
    
    def _handle_slack_keyword(self, data: dict):
        """Handle Slack keyword events."""
        keyword = data.get('keyword')
        logger.info(f"Handling Slack keyword: {keyword}")
        self.dispatcher.dispatch('slack_keyword', data)
    
    def _handle_pr_ready(self, data: dict):
        """Handle PR ready to merge events."""
        repo = data.get('repo')
        pr_number = data.get('number')
        logger.info(f"PR ready to merge: {repo}#{pr_number}")
        
        # Execute configured workflow
        monitoring_config = self.config.get('monitoring', {})
        github_actions = monitoring_config.get('github', {}).get('actions', [])
        
        for action_config in github_actions:
            if action_config.get('trigger') == 'pr_ready_to_merge':
                workflow = action_config.get('workflow')
                if workflow:
                    self.task_queue.add_task(
                        self._execute_workflow,
                        workflow,
                        data
                    )
    
    def _handle_pr_review(self, data: dict):
        """Handle PR needs review events."""
        repo = data.get('repo')
        pr_number = data.get('number')
        logger.info(f"PR needs review: {repo}#{pr_number}")
        
        # Execute configured workflow
        monitoring_config = self.config.get('monitoring', {})
        github_actions = monitoring_config.get('github', {}).get('actions', [])
        
        for action_config in github_actions:
            if action_config.get('trigger') == 'pr_needs_review':
                workflow = action_config.get('workflow')
                if workflow:
                    self.task_queue.add_task(
                        self._execute_workflow,
                        workflow,
                        data
                    )
    
    def _handle_slack_user_mention(self, event: dict):
        """Handle Slack user mention events (user mode)."""
        logger.info("Handling Slack user mention")
        self.dispatcher.dispatch('slack_user_mention', event)
        
        # Execute configured workflow
        monitoring_config = self.config.get('monitoring', {})
        slack_actions = monitoring_config.get('slack', {}).get('actions', [])
        
        for action_config in slack_actions:
            if action_config.get('trigger') == 'user_mention':
                workflow = action_config.get('workflow')
                if workflow:
                    self.task_queue.add_task(
                        self._execute_workflow,
                        workflow,
                        {'event': event}
                    )
    
    def _handle_slack_dm(self, event: dict):
        """Handle Slack DM events (user mode)."""
        logger.info("Handling Slack DM")
        self.dispatcher.dispatch('slack_dm', event)
        
        # Execute configured workflow
        monitoring_config = self.config.get('monitoring', {})
        slack_actions = monitoring_config.get('slack', {}).get('actions', [])
        
        for action_config in slack_actions:
            if action_config.get('trigger') == 'dm_received':
                workflow = action_config.get('workflow')
                if workflow:
                    self.task_queue.add_task(
                        self._execute_workflow,
                        workflow,
                        {'event': event}
                    )
    
    def _handle_user_mentioned_in_pr(self, data: dict):
        """Handle user mentioned in PR events (user mode)."""
        repo = data.get('repo')
        pr_number = data.get('number')
        logger.info(f"User mentioned in PR: {repo}#{pr_number}")
        
        # Execute configured workflow
        monitoring_config = self.config.get('monitoring', {})
        github_actions = monitoring_config.get('github', {}).get('actions', [])
        
        for action_config in github_actions:
            if action_config.get('trigger') == 'user_mentioned_in_pr':
                workflow = action_config.get('workflow')
                if workflow:
                    self.task_queue.add_task(
                        self._execute_workflow,
                        workflow,
                        data
                    )
    
    def _handle_user_assigned_to_pr(self, data: dict):
        """Handle user assigned to PR events (user mode)."""
        repo = data.get('repo')
        pr_number = data.get('number')
        logger.info(f"User assigned to PR: {repo}#{pr_number}")
        
        # Execute configured workflow
        monitoring_config = self.config.get('monitoring', {})
        github_actions = monitoring_config.get('github', {}).get('actions', [])
        
        for action_config in github_actions:
            if action_config.get('trigger') == 'user_assigned_to_pr':
                workflow = action_config.get('workflow')
                if workflow:
                    self.task_queue.add_task(
                        self._execute_workflow,
                        workflow,
                        data
                    )
    
    def _handle_user_notification(self, data: dict):
        """Handle GitHub user notification events (user mode)."""
        notification_id = data.get('id')
        reason = data.get('reason')
        logger.info(f"User notification: {reason} (ID: {notification_id})")
        
        # Execute configured workflow
        monitoring_config = self.config.get('monitoring', {})
        github_actions = monitoring_config.get('github', {}).get('actions', [])
        
        for action_config in github_actions:
            if action_config.get('trigger') == 'user_notification':
                workflow = action_config.get('workflow')
                if workflow:
                    self.task_queue.add_task(
                        self._execute_workflow,
                        workflow,
                        {'notification': data}
                    )
    
    def _main_loop(self):
        """Main daemon loop."""
        logger.info("Entering main loop (press Ctrl+C to stop)")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop()
    
    def stop(self):
        """Stop the daemon."""
        if not self.running:
            return
        
        logger.info("Stopping daemon...")
        self.running = False
        
        # Stop monitors
        for name, monitor in self.monitors.items():
            try:
                monitor.stop()
                logger.info(f"✓ Stopped {name} monitor")
            except Exception as e:
                logger.error(f"Error stopping {name} monitor: {e}")
        
        # Stop scheduler
        if self.scheduler:
            self.scheduler.stop()
            logger.info("✓ Stopped scheduler")
        
        # Stop task queue
        if self.task_queue:
            self.task_queue.stop(wait=True)
            logger.info("✓ Stopped task queue")
        
        logger.info("✓ Daemon stopped")
    
    def get_status(self) -> dict:
        """Get daemon status."""
        return {
            'running': self.running,
            'monitors': {
                name: monitor.is_running()
                for name, monitor in self.monitors.items()
            },
            'scheduler_running': self.scheduler.is_running() if self.scheduler else False,
            'task_queue_stats': self.task_queue.get_stats() if self.task_queue else {},
            'scheduled_jobs': self.scheduler.get_jobs() if self.scheduler else {}
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Production Agent Daemon - Long-running automation system"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/agent_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Load config and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    # Check if config exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found: {args.config}")
        print(f"Example config: config/examples/slack_github_monitor.yaml")
        sys.exit(1)
    
    if args.dry_run:
        print(f"Loading configuration from: {args.config}")
        try:
            config = load_config(args.config)
            print("✓ Configuration loaded successfully")
            print(f"Monitoring enabled: {list(config.get('monitoring', {}).keys())}")
            print(f"Scheduled tasks: {len(config.get('scheduled_tasks', []))}")
            print(f"Workflows: {len(config.get('workflows', {}))}")
            sys.exit(0)
        except Exception as e:
            print(f"✗ Failed to load configuration: {e}")
            sys.exit(1)
    
    # Start daemon
    daemon = AgentDaemon(args.config)
    daemon.start()


if __name__ == '__main__':
    main()
