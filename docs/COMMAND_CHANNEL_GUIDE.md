# Command Channel User Guide

## Overview

The command channel feature allows you to control the agent by sending commands in a dedicated Slack channel. The agent will execute commands and report status updates directly in the channel.

## Quick Start

### 1. Get Your Command Channel ID

1. Open Slack in your browser
2. Navigate to your `#agent-commands` channel (or create one)
3. The channel ID is in the URL: `https://app.slack.com/client/T.../C01234567890`
4. Copy the `C01234567890` part

### 2. Configure

Edit `config/agent_config.yaml`:

```yaml
monitoring:
  slack:
    enabled: true
    mode: user
    user_token: ${SLACK_USER_TOKEN}
    user_id: ${SLACK_USER_ID}
    command_channel: C01234567890  # Your channel ID
    command_prefix: "agent"
```

### 3. Start the Agent

```bash
python agent_daemon.py --config config/agent_config.yaml
```

### 4. Send Commands

In your `#agent-commands` channel:

```
agent help
agent create-pr feature-auth to main
agent check-prs
agent merge-pr #456
```

---

## Available Commands

### GitHub Commands

#### `create-pr` - Create a Pull Request
```
agent create-pr <branch> [to <base>] [--title "Title"]

Examples:
  agent create-pr feature-auth
  agent create-pr feature-auth to main
  agent create-pr fix-bug to develop --title "Fix critical bug"
```

#### `merge-pr` - Merge a Pull Request
```
agent merge-pr <pr_number> [--method squash|merge|rebase]

Examples:
  agent merge-pr 456
  agent merge-pr #456
  agent merge-pr 456 --method squash
```

#### `check-prs` - List Open Pull Requests
```
agent check-prs [repo]

Examples:
  agent check-prs
  agent check-prs myorg/myrepo
```

#### `comment-pr` - Add Comment to PR
```
agent comment-pr <pr_number> <comment>

Examples:
  agent comment-pr 456 LGTM!
  agent comment-pr #456 "Looks good, merging now"
```

### System Commands

#### `help` - Show Help
```
agent help [command]

Examples:
  agent help
  agent help create-pr
```

#### `status` - Show Agent Status
```
agent status

Shows:
  - Agent running status
  - Active monitors
  - Task queue stats
  - Scheduled jobs
```

#### `commands` - List All Commands
```
agent commands

Lists all available commands by category
```

---

## How It Works

### 1. You Send a Command

```
📱 #agent-commands

You: agent create-pr feature-auth to main
```

### 2. Agent Acknowledges

```
Agent: ✓ Starting: Create a pull request...
```

### 3. Agent Executes

The agent:
- Parses your command
- Validates arguments
- Executes the action
- Handles errors

### 4. Agent Reports Result

**Success:**
```
Agent: ✅ Created PR #456: Merge feature-auth into main
       https://github.com/yourorg/repo/pull/456
```

**Error:**
```
Agent: ❌ Failed to create PR
       ```
       Branch 'feature-auth' does not exist
       ```
```

---

## Command Syntax

### Basic Format

```
agent <command> [arguments] [--flags]
```

- **Prefix**: `agent` (configurable)
- **Command**: The action to perform
- **Arguments**: Required and optional parameters
- **Flags**: Optional modifiers starting with `--`

### Quoted Arguments

Use quotes for arguments with spaces:

```
agent comment-pr 456 "This looks great! Approved."
```

### PR Numbers

PR numbers can be specified with or without `#`:

```
agent merge-pr 456
agent merge-pr #456
```

Both work the same way.

---

## Configuration

### Basic Configuration

```yaml
monitoring:
  slack:
    command_channel: C01234567890  # Required
    command_prefix: "agent"        # Optional, default: "agent"
```

### Multiple Channels

Currently, only one command channel is supported. However, you can still receive mentions and DMs in other channels.

### Custom Prefix

Change the command prefix:

```yaml
monitoring:
  slack:
    command_prefix: "bot"  # Now use: bot create-pr ...
```

---

## Tips & Best Practices

### 1. Use a Dedicated Channel

Create a dedicated `#agent-commands` channel:
- Keeps command history organized
- Easy to audit what the agent has done
- Team members can see automation activity

### 2. Check Status Regularly

```
agent status
```

Verify the agent is running and monitors are active.

### 3. Use Help

```
agent help create-pr
```

Get detailed usage for any command.

### 4. Test Commands

Start with safe commands like:
```
agent check-prs
agent help
agent status
```

### 5. Monitor Logs

Check `logs/agent.log` for detailed execution logs.

---

## Troubleshooting

### "Unknown command"

**Problem:** `❌ Unknown command: creat-pr`

**Solution:** Check spelling. Use `agent help` to see available commands.

### "Invalid arguments"

**Problem:** `❌ Invalid arguments for create-pr`

**Solution:** Check usage with `agent help create-pr`

### "No default repository configured"

**Problem:** `❌ No default repository configured`

**Solution:** Add repos to your GitHub config:
```yaml
monitoring:
  github:
    repos:
      - your-org/your-repo
```

### Agent Not Responding

**Checklist:**
1. Is the agent running? Check logs
2. Is the command channel ID correct?
3. Are you using the right prefix?
4. Check `agent status`

### Command Timeout

**Problem:** `❌ Timeout: Command timed out after 300 seconds`

**Solution:** The command took too long. Check logs for details. Some operations (like large PR checks) may need optimization.

---

## Advanced Usage

### Command Aliases

Many commands have aliases:

```
agent pr ...          # Same as: agent create-pr
agent merge ...       # Same as: agent merge-pr
agent prs             # Same as: agent check-prs
agent ?               # Same as: agent help
```

### Combining with Workflows

Commands can trigger workflows:

```yaml
workflows:
  after_pr_created:
    steps:
      - type: slack
        action: send_message
        params:
          channel: dev-team
          message: "New PR created: {pr.url}"
```

---

## Security

### Channel Permissions

- Only users in the command channel can send commands
- Consider making the channel private
- Limit channel membership to trusted team members

### Command Validation

- All commands are validated before execution
- Invalid commands are rejected
- Errors are logged

### Token Security

- Never share your Slack user token
- Store tokens in `.env` file
- Keep `.env` in `.gitignore`

---

## Next Steps

1. **Add More Commands** - See developer guide
2. **Create Workflows** - Automate complex tasks
3. **Set Up Schedules** - Run commands automatically
4. **Monitor Activity** - Check logs and status

For adding custom commands, see: `docs/DEVELOPER_GUIDE.md`
