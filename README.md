# Production AI Agent - Long-Running Automation System

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready, hybrid AI agent that combines deterministic keyboard shortcuts with AI-powered decision making for long-running desktop automation, monitoring, and workflow execution.

## 🌟 Features

### Core Capabilities
- **Hybrid Architecture**: Uses keyboard shortcuts for reliability, AI only when needed
- **Long-Running Daemon**: Continuous operation with event monitoring
- **Event Monitoring**: Real-time Slack and GitHub integration
- **Task Scheduling**: Cron-style and interval-based scheduling
- **Workflow Automation**: YAML-defined workflows with multiple steps
- **REST API**: Optional HTTP API for remote control
- **Rate Limiting**: Prevents API quota exhaustion
- **Response Caching**: Reduces redundant API calls
- **Structured Logging**: JSON logs with rotation

### Integrations
- **Slack**: Monitor messages, mentions, keywords; send automated responses
- **GitHub**: Monitor PRs, auto-merge when approved, notify on reviews
- **AI Providers**: Gemini (primary), OpenAI (fallback)

### Use Cases
- Monitor Slack for urgent messages and respond automatically
- Auto-merge approved GitHub PRs
- Schedule periodic tasks (daily standups, PR checks, etc.)
- Execute complex workflows triggered by events
- Run for hours/days with automatic error recovery

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🚀 Installation

### Prerequisites
- Python 3.7+
- Windows OS (for full functionality)
- API keys for Gemini and/or OpenAI
- (Optional) Slack Bot Token and App Token
- (Optional) GitHub Personal Access Token

### Setup

1. **Clone or download the project**
   ```bash
   cd d:\projects\tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Copy template
   cp .env.example .env
   
   # Edit .env with your API keys
   # IMPORTANT: See SECURITY_NOTICE.md for regenerating exposed keys
   ```

4. **Verify installation**
   ```bash
   python test_suite.py
   ```

## ⚡ Quick Start

### 1. One-Shot Task Execution (Legacy Mode)

```bash
# Open an application
python main.py --goal "Open Notepad"

# Install a package
python main.py --goal "Install requests package"

# Write code with AI
python main.py --goal "Write a Python function to calculate fibonacci"
```

### 2. Long-Running Daemon Mode (NEW)

```bash
# Start daemon with example config
python agent_daemon.py --config config/examples/slack_github_monitor.yaml

# Dry-run to test configuration
python agent_daemon.py --config config/agent_config.yaml --dry-run
```

### 3. REST API Server (Optional)

```bash
# Start API server
python api_server.py --host 0.0.0.0 --port 5000

# Execute task via API
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"goal": "Check Slack for urgent messages"}'

# Get status
curl http://localhost:5000/api/status
```

## ⚙️ Configuration

### Basic Configuration

Create `config/agent_config.yaml`:

```yaml
# Monitoring
monitoring:
  slack:
    enabled: true
    token: ${SLACK_BOT_TOKEN}
    app_token: ${SLACK_APP_TOKEN}
    keywords:
      - urgent
      - help
  
  github:
    enabled: true
    token: ${GITHUB_TOKEN}
    repos:
      - owner/repo-name
    min_approvals: 2

# Scheduled Tasks
scheduled_tasks:
  - name: check_prs
    schedule: "*/15 * * * *"  # Every 15 minutes
    workflow: check_github_prs

# AI Configuration
ai:
  provider: gemini
  model: gemini-2.0-flash-exp
  rate_limit_per_minute: 15
```

See `config/examples/slack_github_monitor.yaml` for a complete example.

### Environment Variables

Required in `.env`:
```bash
# AI Providers
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Slack (optional)
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token

# GitHub (optional)
GITHUB_TOKEN=ghp_your_token
```

## 📖 Usage

### Daemon Mode

The daemon runs continuously, monitoring events and executing scheduled tasks:

```bash
# Start daemon
python agent_daemon.py --config config/agent_config.yaml

# The daemon will:
# - Monitor Slack for mentions/keywords
# - Monitor GitHub for PR events
# - Execute scheduled tasks (cron-style)
# - Run workflows when events occur
# - Log everything to logs/agent.log
```

### Workflows

Define workflows in your config:

```yaml
workflows:
  respond_to_mention:
    steps:
      - type: ai
        action: analyze_message
        params:
          objective: "Analyze and respond to Slack message"
      - type: slack
        action: send_reply
        params:
          use_ai_response: true
  
  auto_merge_pr:
    steps:
      - type: github
        action: merge_pr
        params:
          merge_method: squash
      - type: slack
        action: send_message
        params:
          channel: dev-team
          message: "Auto-merged PR: {pr.title}"
```

### Programmatic Usage

```python
from agent_daemon import AgentDaemon

# Create and start daemon
daemon = AgentDaemon('config/agent_config.yaml')
daemon.start()

# Get status
status = daemon.get_status()
print(status)

# Stop daemon
daemon.stop()
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Agent Daemon                    │
│  (Main orchestrator)                    │
└────────────┬────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐
│Monitors│ │Scheduler│ │Task    │
│        │ │        │ │Queue   │
│-Slack  │ │-Cron   │ │-Workers│
│-GitHub │ │-Interval│ │        │
└────┬───┘ └───┬────┘ └───┬────┘
     │         │           │
     └─────────┼───────────┘
               │
               ▼
      ┌────────────────┐
      │Event Dispatcher│
      └────────┬───────┘
               │
               ▼
      ┌────────────────┐
      │Workflow Engine │
      └────────────────┘
```

### Components

- **Agent Daemon**: Main process, coordinates all components
- **Monitors**: Watch for events (Slack messages, GitHub PRs)
- **Scheduler**: Execute tasks on schedule (cron-style)
- **Task Queue**: Background workers for async execution
- **Event Dispatcher**: Routes events to workflows
- **Workflow Engine**: Executes multi-step workflows
- **Rate Limiter**: Prevents API quota exhaustion
- **Cache**: Reduces redundant API calls

## 🔌 API Reference

### REST API Endpoints

#### Execute Task
```http
POST /api/execute
Content-Type: application/json

{
  "goal": "Open Notepad"
}
```

#### Schedule Task
```http
POST /api/schedule
Content-Type: application/json

{
  "task_id": "daily_check",
  "goal": "Check GitHub PRs",
  "schedule": "0 9 * * *"
}
```

#### Get Status
```http
GET /api/status
```

#### List Jobs
```http
GET /api/jobs
```

See `api_server.py` for complete API documentation.

## 🛠️ Development

### Project Structure

```
d:/projects/tracker/
├── agent/
│   ├── core.py              # Main agent logic
│   ├── brain.py             # AI integration
│   ├── scheduler.py         # Task scheduling
│   ├── event_dispatcher.py  # Event routing
│   └── ...
├── integrations/
│   ├── slack_monitor.py     # Slack integration
│   ├── github_monitor.py    # GitHub integration
│   └── base_monitor.py      # Base monitor class
├── utils/
│   ├── rate_limiter.py      # Rate limiting
│   ├── cache.py             # Response caching
│   ├── task_queue.py        # Background tasks
│   ├── logger.py            # Structured logging
│   └── config_parser.py     # Config management
├── config/
│   └── examples/            # Example configurations
├── agent_daemon.py          # Main daemon
├── api_server.py            # REST API server
└── main.py                  # Legacy CLI
```

### Running Tests

```bash
# Run test suite
python test_suite.py

# Test specific component
python -m pytest tests/test_integrations.py
```

### Adding New Integrations

1. Create monitor class inheriting from `BaseMonitor`
2. Implement `start()` and `stop()` methods
3. Register callbacks for events
4. Add to daemon initialization

Example:
```python
from integrations.base_monitor import BaseMonitor

class MyMonitor(BaseMonitor):
    def start(self, config):
        # Initialize and start monitoring
        pass
    
    def stop(self):
        # Clean shutdown
        pass
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: Daemon won't start
```bash
# Check configuration
python agent_daemon.py --config config/agent_config.yaml --dry-run

# Check logs
tail -f logs/agent.log
```

**Issue**: API rate limits
```bash
# Increase rate limit in config
ai:
  rate_limit_per_minute: 10  # Lower value
```

**Issue**: Slack/GitHub not working
```bash
# Verify tokens in .env
cat .env | grep TOKEN

# Check monitor logs
grep "Slack\|GitHub" logs/agent.log
```

### Debug Mode

Enable detailed logging:
```yaml
logging:
  level: DEBUG
  file: logs/agent.log
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📞 Support

- Documentation: See `docs/` directory
- Issues: Create a GitHub issue
- Security: See `SECURITY_NOTICE.md`

## 🎯 Roadmap

- [ ] Email integration
- [ ] Webhook support
- [ ] Web dashboard
- [ ] Docker containerization
- [ ] Cloud deployment guides
- [ ] More AI providers (Claude, etc.)

---

**Built with ❤️ for production automation**
