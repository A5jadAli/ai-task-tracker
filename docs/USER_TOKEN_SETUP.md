# User Token Setup Guide

This guide explains how to obtain and configure personal account tokens for Slack and GitHub integration, allowing the agent to act on behalf of YOUR personal accounts.

## Table of Contents

- [Slack User Token Setup](#slack-user-token-setup)
- [GitHub Personal Access Token Setup](#github-personal-access-token-setup)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Slack User Token Setup

### Prerequisites

- Admin access to your Slack workspace (or permission to create apps)
- A Slack workspace where you want the agent to operate

### Step-by-Step Instructions

#### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter app name (e.g., "Personal AI Agent")
5. Select your workspace
6. Click **"Create App"**

#### 2. Configure OAuth Scopes

1. In your app settings, go to **"OAuth & Permissions"** (left sidebar)
2. Scroll down to **"User Token Scopes"** section
3. Click **"Add an OAuth Scope"** and add the following scopes:

   **Required Scopes:**
   - `users:read` - View people in workspace
   - `channels:read` - View basic channel info
   - `channels:history` - View messages in public channels
   - `chat:write` - Send messages as you
   - `groups:read` - View basic private channel info
   - `groups:history` - View messages in private channels
   - `im:read` - View basic DM info
   - `im:history` - View messages in DMs
   - `mpim:read` - View basic group DM info
   - `mpim:history` - View messages in group DMs

#### 3. Enable Socket Mode

1. Go to **"Socket Mode"** (left sidebar)
2. Toggle **"Enable Socket Mode"** to ON
3. Enter a token name (e.g., "Agent Socket Token")
4. Click **"Generate"**
5. **Copy the App-Level Token** (starts with `xapp-`) - this is your `SLACK_APP_TOKEN`
6. Click **"Done"**

#### 4. Enable Event Subscriptions

1. Go to **"Event Subscriptions"** (left sidebar)
2. Toggle **"Enable Events"** to ON
3. Under **"Subscribe to bot events"**, add:
   - `message.channels` - Messages in public channels
   - `message.groups` - Messages in private channels
   - `message.im` - Direct messages
   - `message.mpim` - Group direct messages
4. Click **"Save Changes"**

#### 5. Install App to Workspace

1. Go to **"OAuth & Permissions"** (left sidebar)
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. **Copy the User OAuth Token** (starts with `xoxp-`) - this is your `SLACK_USER_TOKEN`

#### 6. Get Your Slack User ID

**Method 1: From Slack App**
1. Open Slack desktop or web app
2. Click your profile picture (top right)
3. Click **"Profile"**
4. Click **"More"** (three dots)
5. Click **"Copy member ID"**
6. This is your `SLACK_USER_ID` (format: `U01234567890`)

**Method 2: From API**
```bash
curl -H "Authorization: Bearer YOUR_USER_TOKEN" \
  https://slack.com/api/auth.test
```
Look for the `user_id` field in the response.

---

## GitHub Personal Access Token Setup

### Prerequisites

- A GitHub account
- Access to repositories you want to monitor

### Step-by-Step Instructions

#### 1. Navigate to Token Settings

1. Go to [https://github.com/settings/tokens/new](https://github.com/settings/tokens/new)
2. Or: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token

#### 2. Configure Token

1. **Note**: Enter a descriptive name (e.g., "AI Task Tracker Agent")
2. **Expiration**: Select expiration period (recommend 90 days for security)
3. **Select scopes**: Check the following boxes:

   **Required Scopes:**
   - ✅ `repo` - Full control of private repositories
     - Includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
   - ✅ `notifications` - Access notifications
   - ✅ `read:user` - Read user profile data
   - ✅ `read:org` - Read org and team membership, read org projects

   **Optional Scopes (for additional features):**
   - `workflow` - Update GitHub Action workflows (if you want to trigger workflows)
   - `write:discussion` - Read and write discussions

#### 3. Generate Token

1. Scroll to bottom and click **"Generate token"**
2. **IMPORTANT**: Copy the token immediately (starts with `ghp_`)
3. This is your `GITHUB_PERSONAL_TOKEN`
4. **You won't be able to see it again!** Store it securely.

#### 4. Get Your GitHub Username

Your GitHub username is the name in your profile URL:
- If your profile is `github.com/johndoe`, your username is `johndoe`
- This is your `GITHUB_USERNAME`

---

## Configuration

### 1. Update `.env` File

Copy `.env.example` to `.env` if you haven't already:

```bash
cp .env.example .env
```

Edit `.env` and add your tokens:

```bash
# Slack User Token Configuration
SLACK_USER_TOKEN=xoxp-YOUR-USER-TOKEN-HERE
SLACK_USER_ID=U01234567890
SLACK_APP_TOKEN=xapp-YOUR-APP-TOKEN-HERE

# GitHub Personal Token Configuration
GITHUB_PERSONAL_TOKEN=ghp_YOUR_PERSONAL_TOKEN_HERE
GITHUB_USERNAME=your-github-username
```

### 2. Update Agent Configuration

Create or edit `config/agent_config.yaml`:

```yaml
monitoring:
  slack:
    enabled: true
    mode: user                        # Use 'user' mode for personal account
    user_token: ${SLACK_USER_TOKEN}
    user_id: ${SLACK_USER_ID}
    monitor_dms: true
    keywords:
      - urgent
      - help
    actions:
      - trigger: user_mention
        workflow: respond_to_mention
      - trigger: dm_received
        workflow: respond_to_dm

  github:
    enabled: true
    mode: user                                    # Use 'user' mode for personal account
    personal_token: ${GITHUB_PERSONAL_TOKEN}
    username: ${GITHUB_USERNAME}
    repos:
      - your-org/your-repo
    monitor_user_notifications: true
    monitor_user_mentions: true
    actions:
      - trigger: user_mentioned_in_pr
        workflow: respond_to_pr_mention
      - trigger: user_assigned_to_pr
        workflow: handle_pr_assignment
```

---

## Testing

### 1. Validate Configuration

Run a dry-run to validate your configuration:

```bash
python agent_daemon.py --config config/agent_config.yaml --dry-run
```

Expected output:
```
✓ Configuration loaded successfully
Monitoring enabled: ['slack', 'github']
Scheduled tasks: 0
Workflows: X
```

### 2. Start the Daemon

```bash
python agent_daemon.py --config config/agent_config.yaml
```

Look for these log messages:
```
✓ Slack monitor started in user mode
Authenticated as user: U01234567890
✓ GitHub monitor started in user mode
Authenticated as GitHub user: your-username
```

### 3. Test Slack Integration

**Test 1: User Mention**
1. Have someone mention you in a Slack channel: `@yourname hello`
2. Check logs for: `User mentioned in channel ...`
3. Verify the configured workflow executes

**Test 2: Direct Message**
1. Send yourself a DM or have someone DM you
2. Check logs for: `DM received from user ...`
3. Verify the configured workflow executes

### 4. Test GitHub Integration

**Test 1: PR Mention**
1. Create a test PR and mention yourself in the description: `@your-username please review`
2. Check logs for: `User mentioned in PR: repo#123`
3. Verify the configured workflow executes

**Test 2: PR Assignment**
1. Assign yourself to a PR
2. Check logs for: `User assigned to PR: repo#123`
3. Verify the configured workflow executes

---

## Troubleshooting

### Slack Issues

#### "Slack tokens not configured for user mode"
- **Cause**: Missing `SLACK_USER_TOKEN` or `SLACK_APP_TOKEN`
- **Solution**: Verify tokens are in `.env` file and start with correct prefixes (`xoxp-` and `xapp-`)

#### "Failed to get user ID for user mode"
- **Cause**: User token doesn't have `users:read` scope
- **Solution**: Go back to Slack app settings and add the `users:read` scope

#### "User mentions not detected"
- **Cause**: Incorrect `SLACK_USER_ID`
- **Solution**: Verify your user ID by copying it from your Slack profile

#### "Socket mode connection failed"
- **Cause**: Socket mode not enabled or invalid app token
- **Solution**: Enable Socket Mode in Slack app settings and regenerate app token

### GitHub Issues

#### "GitHub token not configured for user mode"
- **Cause**: Missing `GITHUB_PERSONAL_TOKEN`
- **Solution**: Verify token is in `.env` file and starts with `ghp_`

#### "Failed to authenticate"
- **Cause**: Invalid or expired token
- **Solution**: Generate a new personal access token with required scopes

#### "User mentions not detected in PRs"
- **Cause**: Incorrect `GITHUB_USERNAME`
- **Solution**: Verify your GitHub username matches your profile

#### "403 Forbidden" errors
- **Cause**: Token doesn't have required scopes
- **Solution**: Regenerate token with `repo`, `notifications`, `read:user`, and `read:org` scopes

### General Issues

#### "Rate limit exceeded"
- **Cause**: Too many API calls
- **Solution**: Increase `poll_interval` in GitHub config or reduce `rate_limit_per_minute` in AI config

#### "Workflows not executing"
- **Cause**: Workflow name mismatch or missing workflow definition
- **Solution**: Verify workflow names in `actions` match workflow definitions in `workflows` section

---

## Security Best Practices

1. **Never commit `.env` file** - It's in `.gitignore`, keep it there
2. **Use token expiration** - Set GitHub tokens to expire after 90 days
3. **Rotate tokens regularly** - Generate new tokens periodically
4. **Limit scopes** - Only grant minimum required permissions
5. **Monitor token usage** - Check GitHub settings for token activity
6. **Revoke unused tokens** - Remove old tokens from GitHub/Slack settings

---

## Next Steps

Once configured:

1. **Customize workflows** - Edit workflows in `config/agent_config.yaml`
2. **Add scheduled tasks** - Set up cron-style tasks for periodic checks
3. **Monitor logs** - Check `logs/agent.log` for activity
4. **Adjust settings** - Fine-tune polling intervals and rate limits

For more information, see:
- [README.md](../README.md) - General documentation
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [config/examples/slack_github_monitor.yaml](../config/examples/slack_github_monitor.yaml) - Example configuration
