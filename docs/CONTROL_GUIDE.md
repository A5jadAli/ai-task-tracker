# How to Control and Command the Agent

This guide explains all the ways you can control and give commands to the AI Task Tracker agent.

## Table of Contents

- [Current Control Methods](#current-control-methods)
- [Adding Interactive Commands](#adding-interactive-commands)
- [Example Use Cases](#example-use-cases)
- [Limitations](#limitations)

---

## Current Control Methods

### 1. Event-Driven Automation (Reactive)

The agent automatically responds to events without you explicitly commanding it.

#### Slack Events

**User Mentions:**
```
Someone: @yourname can you check the deployment logs?
Agent: [Automatically detects mention and executes configured workflow]
```

**Direct Messages:**
```
Someone DMs you: "Hey, need help with the API"
Agent: [Automatically detects DM and can respond]
```

**Keywords:**
```
Someone: "This is urgent! The server is down"
Agent: [Detects keyword "urgent" and triggers alert workflow]
```

**Configuration:**
```yaml
# config/agent_config.yaml
monitoring:
  slack:
    mode: user
    user_token: ${SLACK_USER_TOKEN}
    user_id: ${SLACK_USER_ID}
    monitor_dms: true
    keywords:
      - urgent
      - help
      - agent
    actions:
      - trigger: user_mention
        workflow: respond_to_mention
      - trigger: dm_received
        workflow: respond_to_dm
      - trigger: keyword
        workflow: handle_urgent
```

#### GitHub Events

**PR Mentions:**
```
Someone mentions you in PR: "@yourname please review the auth changes"
Agent: [Automatically detects and can comment/review]
```

**PR Assignments:**
```
You're assigned to PR #123
Agent: [Automatically notifies you on Slack or takes action]
```

**Notifications:**
```
You get a GitHub notification
Agent: [Processes and can summarize or act on it]
```

**Configuration:**
```yaml
monitoring:
  github:
    mode: user
    personal_token: ${GITHUB_PERSONAL_TOKEN}
    username: ${GITHUB_USERNAME}
    repos:
      - your-org/your-repo
    monitor_user_mentions: true
    monitor_user_notifications: true
    actions:
      - trigger: user_mentioned_in_pr
        workflow: acknowledge_pr_mention
      - trigger: user_assigned_to_pr
        workflow: review_assigned_pr
```

---

### 2. Scheduled Tasks (Proactive)

The agent runs tasks on a schedule using cron syntax.

**Examples:**

```yaml
scheduled_tasks:
  # Daily standup reminder
  - name: daily_standup
    schedule: "0 9 * * 1-5"  # 9 AM on weekdays
    workflow: send_standup_reminder
  
  # Check PRs every 15 minutes
  - name: check_prs
    schedule: "*/15 * * * *"
    workflow: check_and_notify_prs
  
  # Weekly summary
  - name: weekly_summary
    schedule: "0 17 * * 5"  # 5 PM every Friday
    workflow: send_weekly_summary
```

**Workflow Example:**
```yaml
workflows:
  send_standup_reminder:
    steps:
      - type: slack
        action: send_message
        params:
          channel: general
          message: "Daily standup in 30 minutes! 🚀"
  
  check_and_notify_prs:
    steps:
      - type: github
        action: check_all_prs
      - type: slack
        action: send_message
        params:
          channel: dev-team
          message: "Found {pr_count} open PRs needing review"
```

---

### 3. REST API (Direct Commands)

Send commands via HTTP API for programmatic control.

#### Start API Server

```bash
python api_server.py --host 0.0.0.0 --port 5000
```

#### Execute Task

```bash
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Check all open PRs in myorg/myrepo and summarize them"
  }'
```

#### Schedule Task

```bash
curl -X POST http://localhost:5000/api/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "daily_check",
    "goal": "Check GitHub PRs",
    "schedule": "0 9 * * *"
  }'
```

#### Get Status

```bash
curl http://localhost:5000/api/status
```

#### List Jobs

```bash
curl http://localhost:5000/api/jobs
```

---

### 4. Command Line (One-off Tasks)

Run single tasks directly from the command line.

```bash
# Open an application
python main.py --goal "Open VSCode"

# Install a package
python main.py --goal "Install the requests package using pip"

# Write code
python main.py --goal "Write a Python function to calculate fibonacci"

# Complex task
python main.py --goal "Create a new GitHub PR for branch feature-auth"
```

---

## Adding Interactive Commands

### What's Missing?

Currently, you **cannot** send ad-hoc commands through Slack or GitHub like:

❌ "Agent, create a PR for branch feature-x"  
❌ "Agent, summarize all my notifications"  
❌ "Agent, merge PR #123"  
❌ "Agent, what's the status of the deployment?"

### How to Add Command Support

You can add a command parser to detect commands in messages. Here's how:

#### Option 1: Keyword-Based Commands

**Add to your config:**
```yaml
monitoring:
  slack:
    mode: user
    commands:
      enabled: true
      prefix: "agent"  # Commands start with "agent"
      allowed_users:  # Optional: restrict who can command
        - U01234567890  # Your user ID
    actions:
      - trigger: command
        workflow: execute_command
```

**Example usage:**
```
You: agent create pr for feature-auth
You: agent merge pr #123
You: agent summarize notifications
You: agent check deployment status
```

#### Option 2: Slash Commands (Slack)

Create a Slack slash command `/agent`:

```
/agent create pr for feature-auth
/agent merge pr #123
/agent help
```

#### Option 3: Natural Language Commands

Use AI to parse natural language:

```
You: @agent can you create a PR for the feature-auth branch?
Agent: [AI parses intent and executes]

You: @agent what's the status of PR #123?
Agent: [AI fetches and responds]
```

---

## Example Use Cases

### Use Case 1: Automated PR Review Notifications

**Scenario:** You want to be notified on Slack when you're mentioned in a PR.

**Configuration:**
```yaml
monitoring:
  github:
    mode: user
    actions:
      - trigger: user_mentioned_in_pr
        workflow: notify_slack_pr_mention

workflows:
  notify_slack_pr_mention:
    steps:
      - type: slack
        action: send_dm
        params:
          user_id: ${SLACK_USER_ID}
          message: "You were mentioned in PR: {pr.title} - {pr.url}"
```

**Result:** Automatic Slack DM when mentioned in GitHub PR.

---

### Use Case 2: Daily PR Summary

**Scenario:** Get a daily summary of open PRs at 9 AM.

**Configuration:**
```yaml
scheduled_tasks:
  - name: daily_pr_summary
    schedule: "0 9 * * 1-5"
    workflow: send_pr_summary

workflows:
  send_pr_summary:
    steps:
      - type: ai
        action: analyze_prs
        params:
          objective: "Summarize all open PRs and their status"
      - type: slack
        action: send_message
        params:
          channel: dev-team
          message: "{ai_response}"
```

**Result:** Daily automated PR summary in Slack.

---

### Use Case 3: Auto-Respond to Urgent Messages

**Scenario:** Auto-respond when someone DMs you with "urgent".

**Configuration:**
```yaml
monitoring:
  slack:
    mode: user
    keywords:
      - urgent
    actions:
      - trigger: keyword
        workflow: handle_urgent_dm

workflows:
  handle_urgent_dm:
    steps:
      - type: ai
        action: analyze_message
        params:
          objective: "Analyze urgent message and provide helpful response"
      - type: slack
        action: send_reply
        params:
          use_ai_response: true
```

**Result:** AI analyzes urgent messages and responds automatically.

---

### Use Case 4: Manual Command via API

**Scenario:** Trigger a task from your own script.

```python
import requests

# Send command to agent
response = requests.post('http://localhost:5000/api/execute', json={
    'goal': 'Check all open PRs and create a summary report'
})

print(response.json())
```

**Result:** Programmatic control from your scripts.

---

## Limitations

### Current Limitations

1. **No Interactive Command Parser** - Can't send free-form commands like "agent do X"
2. **No Conversation Context** - Each event is handled independently
3. **No Command History** - Can't reference previous commands
4. **Limited AI Decision Making** - Workflows are predefined, not dynamic

### Workarounds

**For Ad-Hoc Commands:**
- Use the REST API with curl/scripts
- Use the command line `main.py --goal "..."`
- Set up keyword triggers for common commands

**For Interactive Control:**
- Use Slack keywords: "urgent", "help", "agent"
- Mention yourself in messages to trigger workflows
- Send DMs to trigger DM workflows

---

## Recommended Setup

### For Personal Use

```yaml
monitoring:
  slack:
    mode: user
    monitor_dms: true
    keywords:
      - urgent
      - help
      - deploy
      - error
    actions:
      - trigger: user_mention
        workflow: ai_respond
      - trigger: dm_received
        workflow: ai_respond
      - trigger: keyword
        workflow: alert_and_respond

  github:
    mode: user
    monitor_user_mentions: true
    monitor_user_notifications: true
    actions:
      - trigger: user_mentioned_in_pr
        workflow: acknowledge_pr
      - trigger: user_assigned_to_pr
        workflow: notify_slack

scheduled_tasks:
  - name: morning_summary
    schedule: "0 9 * * 1-5"
    workflow: send_daily_summary

workflows:
  ai_respond:
    steps:
      - type: ai
        action: analyze_message
        params:
          objective: "Analyze message and provide helpful response"
      - type: slack
        action: send_reply
        params:
          use_ai_response: true
```

---

## Next Steps

1. **Configure your workflows** - Define what happens for each trigger
2. **Test with keywords** - Use keywords to trigger actions
3. **Set up schedules** - Automate recurring tasks
4. **Use the API** - For programmatic control
5. **Consider adding command parser** - For interactive commands

---

## Want Interactive Commands?

If you want to add a command parser so you can say things like:

```
You: agent create pr for feature-auth
You: agent merge pr #123
You: agent summarize my notifications
```

Let me know and I can implement a command parsing system that:
- Detects command patterns in messages
- Parses command arguments
- Executes corresponding actions
- Responds with results

This would make the agent much more interactive and controllable!
