# Required Tokens for Personal Account Integration

## Quick Reference

Add these tokens to your `.env` file to enable personal account mode:

```bash
# ============================================================================
# SLACK - Personal Account Mode
# ============================================================================

# Your personal Slack user token (starts with xoxp-)
# Get from: https://api.slack.com/apps -> Your App -> OAuth & Permissions -> User OAuth Token
SLACK_USER_TOKEN=xoxp-your-user-token-here

# Your Slack user ID (starts with U, format: U01234567890)
# Get from: Slack Profile -> More -> Copy member ID
SLACK_USER_ID=U01234567890

# Slack app-level token for Socket Mode (starts with xapp-)
# Get from: https://api.slack.com/apps -> Your App -> Socket Mode -> Generate Token
SLACK_APP_TOKEN=xapp-your-app-token-here

# ============================================================================
# GITHUB - Personal Account Mode
# ============================================================================

# Your GitHub personal access token (starts with ghp_)
# Get from: https://github.com/settings/tokens/new
# Required scopes: repo, notifications, read:user, read:org
GITHUB_PERSONAL_TOKEN=ghp_your-personal-access-token-here

# Your GitHub username (e.g., if your profile is github.com/johndoe, use "johndoe")
GITHUB_USERNAME=your-github-username
```

---

## Detailed Setup Instructions

For step-by-step instructions on obtaining these tokens, see:
**[docs/USER_TOKEN_SETUP.md](docs/USER_TOKEN_SETUP.md)**

---

## Configuration

After adding tokens to `.env`, update your agent configuration:

```yaml
# config/agent_config.yaml
monitoring:
  slack:
    enabled: true
    mode: user                        # Enable user mode
    user_token: ${SLACK_USER_TOKEN}
    user_id: ${SLACK_USER_ID}
    monitor_dms: true

  github:
    enabled: true
    mode: user                        # Enable user mode
    personal_token: ${GITHUB_PERSONAL_TOKEN}
    username: ${GITHUB_USERNAME}
    monitor_user_notifications: true
    monitor_user_mentions: true
```

---

## Testing

Validate your configuration:

```bash
python agent_daemon.py --config config/agent_config.yaml --dry-run
```

Start the daemon:

```bash
python agent_daemon.py --config config/agent_config.yaml
```

---

## What This Enables

### Slack ✅
- ✅ Monitor when **YOU** are mentioned (not just the bot)
- ✅ Respond **as YOU** (messages appear from your account)
- ✅ Monitor and respond to **your DMs**

### GitHub ✅
- ✅ Monitor when **YOU** are mentioned in PRs
- ✅ Monitor when **YOU** are assigned to PRs
- ✅ Monitor **your GitHub notifications**
- ✅ Comment and merge **as YOU**

---

## Need Help?

- **Setup Guide**: [docs/USER_TOKEN_SETUP.md](docs/USER_TOKEN_SETUP.md)
- **Example Config**: [config/examples/slack_github_monitor.yaml](config/examples/slack_github_monitor.yaml)
- **Implementation Details**: See walkthrough.md in artifacts directory
