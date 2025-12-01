# 🚀 Quick Start Guide

## Get Started in 5 Minutes

### Step 1: Verify Installation ✅

Dependencies are already installed! Verify:
```bash
python -c "import slack_sdk, github, apscheduler; print('✓ All dependencies installed')"
```

### Step 2: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your API keys
# IMPORTANT: Regenerate your exposed API keys first! (see SECURITY_NOTICE.md)
```

Minimum required in `.env`:
```bash
GEMINI_API_KEY=your_new_key_here
MODEL_PROVIDER=gemini
MODEL_NAME=gemini-2.0-flash-exp
```

### Step 3: Test Basic Functionality

```bash
# Test the fixed bugs
python demo_agent.py
# Select option 1 - Should now work correctly!
```

### Step 4: Try the Daemon (Long-Running Mode)

```bash
# Test configuration
python agent_daemon.py --config config/examples/slack_github_monitor.yaml --dry-run

# If you have Slack/GitHub tokens, start the daemon:
python agent_daemon.py --config config/examples/slack_github_monitor.yaml
```

### Step 5: Try the API Server

```bash
# Terminal 1: Start API server
python api_server.py

# Terminal 2: Test it
curl http://localhost:5000/api/health
curl http://localhost:5000/api/status

# Execute a task
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"goal": "Open Notepad"}'
```

---

## 🎯 Common Use Cases

### Use Case 1: Monitor Slack for 2-3 Hours

**Setup:**
1. Get Slack Bot Token and App Token from https://api.slack.com/apps
2. Add to `.env`:
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_APP_TOKEN=xapp-your-token
   ```
3. Create `config/my_slack_config.yaml`:
   ```yaml
   monitoring:
     slack:
       enabled: true
       token: ${SLACK_BOT_TOKEN}
       app_token: ${SLACK_APP_TOKEN}
       keywords:
         - urgent
         - help
   
   workflows:
     respond_to_mention:
       steps:
         - type: ai
           action: analyze_message
         - type: slack
           action: send_reply
   ```

**Run:**
```bash
python agent_daemon.py --config config/my_slack_config.yaml
```

The daemon will:
- Monitor Slack continuously
- Respond to @mentions with AI
- Detect keywords and alert you
- Run for as long as you need

### Use Case 2: Auto-Merge GitHub PRs

**Setup:**
1. Get GitHub Personal Access Token from https://github.com/settings/tokens
2. Add to `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_token
   ```
3. Create `config/my_github_config.yaml`:
   ```yaml
   monitoring:
     github:
       enabled: true
       token: ${GITHUB_TOKEN}
       repos:
         - your-org/your-repo
       poll_interval: 300  # 5 minutes
       min_approvals: 2
       require_ci_pass: true
   
   workflows:
     auto_merge_pr:
       steps:
         - type: github
           action: merge_pr
           params:
             merge_method: squash
   ```

**Run:**
```bash
python agent_daemon.py --config config/my_github_config.yaml
```

The daemon will:
- Check PRs every 5 minutes
- Auto-merge when approved + CI passes
- Run indefinitely

### Use Case 3: Scheduled Tasks

**Setup:**
Create `config/my_schedule_config.yaml`:
```yaml
scheduled_tasks:
  - name: morning_check
    schedule: "0 9 * * 1-5"  # 9 AM weekdays
    workflow: morning_routine
  
  - name: hourly_check
    schedule: "0 * * * *"  # Every hour
    workflow: hourly_tasks

workflows:
  morning_routine:
    steps:
      - type: log
        params:
          message: "Good morning! Starting daily tasks..."
  
  hourly_tasks:
    steps:
      - type: log
        params:
          message: "Hourly check complete"
```

**Run:**
```bash
python agent_daemon.py --config config/my_schedule_config.yaml
```

---

## 🔧 Troubleshooting

### Issue: "Configuration file not found"
```bash
# Use absolute path or check current directory
python agent_daemon.py --config "$(pwd)/config/agent_config.yaml"
```

### Issue: "Slack/GitHub monitor failed to start"
```bash
# Check tokens are set
cat .env | grep TOKEN

# Test configuration
python agent_daemon.py --config config/agent_config.yaml --dry-run
```

### Issue: "Rate limit exceeded"
```bash
# Lower rate limit in config
ai:
  rate_limit_per_minute: 10  # Reduce from 15
```

### Issue: "Process not found" (for app detection)
```bash
# Check process name
Get-Process | Select-Object Name | findstr notepad

# The fixed code should handle this now!
```

---

## 📚 Next Steps

1. **Read the README**: `README.md` has complete documentation
2. **Review Examples**: Check `config/examples/` for more configs
3. **Check Security**: Read `SECURITY_NOTICE.md` and regenerate API keys
4. **Explore Code**: All code is well-documented with docstrings
5. **Customize**: Create your own workflows and scheduled tasks

---

## 💡 Pro Tips

1. **Start Simple**: Begin with just one integration (Slack OR GitHub)
2. **Test Workflows**: Use `--dry-run` to test configurations
3. **Monitor Logs**: Check `logs/agent.log` for detailed info
4. **Use API**: Control daemon remotely via REST API
5. **Graceful Shutdown**: Always use Ctrl+C to stop daemon

---

## 🎉 You're Ready!

Your production agent is now capable of:
- ✅ Running for hours/days continuously
- ✅ Monitoring Slack and GitHub
- ✅ Executing scheduled tasks
- ✅ Auto-responding with AI
- ✅ Auto-merging PRs
- ✅ Running custom workflows

**Happy Automating!** 🚀
