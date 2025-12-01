#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
REST API Server for remote agent control.

Provides HTTP endpoints for:
- Task execution
- Status monitoring
- Scheduler management
- Configuration updates
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify
from flask_cors import CORS
from agent.core import AutonomousAgent
from agent.scheduler import TaskScheduler
from utils.logger import setup_logger, get_logger
from utils.config_parser import load_config

# Setup
app = Flask(__name__)
CORS(app)
logger = setup_logger('api_server', 'logs/api.log')

# Global instances
agent = None
scheduler = None
config = None


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0'
    })


@app.route('/api/execute', methods=['POST'])
def execute_task():
    """
    Execute a task.
    
    Request body:
    {
        "goal": "Open Notepad"
    }
    """
    try:
        data = request.json
        goal = data.get('goal')
        
        if not goal:
            return jsonify({'error': 'Missing goal parameter'}), 400
        
        logger.info(f"API: Executing task: {goal}")
        
        # Execute task
        success = agent.run(goal)
        
        return jsonify({
            'success': success,
            'goal': goal,
            'state': agent.state_machine.current_state.value
        })
    
    except Exception as e:
        logger.error(f"Error executing task: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedule', methods=['POST'])
def schedule_task():
    """
    Schedule a task.
    
    Request body:
    {
        "task_id": "my_task",
        "goal": "Check GitHub PRs",
        "schedule": "*/15 * * * *"  // cron expression
    }
    """
    try:
        data = request.json
        task_id = data.get('task_id')
        goal = data.get('goal')
        schedule_expr = data.get('schedule')
        
        if not all([task_id, goal, schedule_expr]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Create task function
        def task_func():
            logger.info(f"Scheduled task executing: {goal}")
            agent.run(goal)
        
        # Add to scheduler
        job = scheduler.add_cron_task(task_id, task_func, schedule_expr)
        
        if job:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'next_run': str(job.next_run_time)
            })
        else:
            return jsonify({'error': 'Failed to schedule task'}), 500
    
    except Exception as e:
        logger.error(f"Error scheduling task: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedule/<task_id>', methods=['DELETE'])
def remove_scheduled_task(task_id):
    """Remove a scheduled task."""
    try:
        success = scheduler.remove_task(task_id)
        
        return jsonify({
            'success': success,
            'task_id': task_id
        })
    
    except Exception as e:
        logger.error(f"Error removing task: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get agent status."""
    try:
        return jsonify({
            'agent_state': agent.state_machine.current_state.value,
            'scheduler_running': scheduler.is_running(),
            'scheduled_jobs': scheduler.get_jobs(),
            'task_history_count': len(agent.history)
        })
    
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all scheduled jobs."""
    try:
        jobs = scheduler.get_jobs()
        return jsonify({'jobs': jobs})
    
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration (sanitized)."""
    try:
        # Return config without sensitive data
        safe_config = config.to_dict()
        
        # Remove sensitive keys
        if 'monitoring' in safe_config:
            for service in safe_config['monitoring'].values():
                if isinstance(service, dict):
                    service.pop('token', None)
                    service.pop('app_token', None)
        
        return jsonify(safe_config)
    
    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent API Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--config', default='config/agent_config.yaml', help='Config file')
    
    args = parser.parse_args()
    
    # Initialize global instances
    global agent, scheduler, config
    
    logger.info("Initializing API server...")
    
    # Load config
    if os.path.exists(args.config):
        config = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")
    else:
        logger.warning(f"Config file not found: {args.config}")
        config = load_config.__new__(load_config.__class__)
        config.config = {}
    
    # Initialize components
    agent = AutonomousAgent()
    scheduler = TaskScheduler()
    scheduler.start()
    
    logger.info(f"Starting API server on {args.host}:{args.port}")
    
    # Run server
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
