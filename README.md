# Email Summary Agent

An AI-powered Gmail summarization system built with LangGraph that automatically fetches, classifies, and summarizes emails with intelligent event detection and Slack notifications.

## Overview

This system integrates Gmail API, Google Calendar API, OpenAI GPT-4o, and LangGraph to create an intelligent email processing workflow that:
- Fetches emails from one or multiple Gmail accounts
- Classifies email importance using AI (High/Medium/Low)
- Generates structured daily summaries
- Detects calendar events from email content
- Sends formatted reports via Slack
- Creates Google Calendar events with interactive confirmation

## Key Features

- **AI-Powered Classification**: Automatically categorizes emails by importance
- **Intelligent Summarization**: Extracts key information to save reading time
- **Event Detection**: Identifies calendar events from email content with confidence scoring
- **Interactive Confirmations**: Slack button-based approval for calendar events
- **Multi-Account Support**: Process emails from up to 3 Gmail accounts simultaneously
- **Stateful Workflows**: LangGraph with SQLite persistence for resumable execution
- **Slack Integration**: Rich notifications with markdown formatting
- **Easy Deployment**: Free deployment via GitHub Actions or Render
- **Scheduled Execution**: Daily automated runs with cron triggers

## Project Structure

```
email-summary-agent/
├── main.py                          # Direct execution entry point
├── init_credentials.py              # Initialize credentials from base64 env vars
├── init_calendar_credentials.py     # OAuth flow for Google Calendar
├── encode_credentials.py            # Convert credentials to base64 for deployment
├── authorize_accounts.py            # Multi-account Gmail authorization
├── requirements.txt                 # Python dependencies
├── langgraph.json                   # LangGraph configuration
│
├── agent/
│   ├── __init__.py
│   └── graph.py                     # LangGraph workflow definition (8 nodes)
│
├── services/
│   ├── __init__.py
│   ├── gmail_service.py             # Gmail API (single & multi-account)
│   ├── ai_service.py                # OpenAI GPT-4o classification & summarization
│   ├── calendar_service.py          # Google Calendar event creation
│   ├── event_service.py             # AI-powered event detection
│   └── slack_service.py             # Slack notifications & interactive messages
│
├── api/
│   └── server.py                    # FastAPI server for webhooks
│
├── .github/workflows/
│   └── email-summary.yml            # GitHub Actions daily trigger
│
└── credentials/                     # OAuth credentials (gitignored)
    ├── credentials.json             # Single account OAuth credentials
    ├── token.json                   # Single account token
    ├── credentials_account*.json    # Multi-account credentials
    ├── token_account*.json          # Multi-account tokens
    └── calendar_token.json          # Calendar API token
```

## System Workflow

The system implements an 8-node LangGraph workflow:

```
START
  ↓
[1] fetch_emails
    • Fetches emails from Gmail API (supports single & multi-account)
    • Filters by time range (24h, 7d, 30d, etc.)
    • Decodes message bodies (plain text & HTML)
  ↓
[2] classify_importance
    • GPT-4o categorizes emails as High/Medium/Low
    • Uses structured output with Pydantic models
    • Prioritizes job interviews, school announcements, etc.
  ↓
[3] summarize_content
    • GPT-4o creates structured daily summary
    • Organized by: Job-related, School-related, Other important
    • Includes overall email overview
  ↓
[4] detect_events
    • AI extracts calendar events with confidence scores
    • Filters events with confidence ≥ 0.7
    • Extracts: title, time, location, description
  ↓
[5] generate_report
    • Formats classified emails into markdown report
    • Includes statistics and email counts
    • Ready for Slack rendering
  ↓
[6] send_notification
    • Posts report to Slack via webhook
    • Converts markdown to Slack mrkdwn format
  ↓
[Conditional] Has events with confidence ≥ 0.7?
  ├─ YES → [7] request_confirmation
  │          • Posts interactive Slack message with buttons
  │          • Per-event "Confirm" / "Skip" actions
  │          • Workflow pauses waiting for user input
  │          ↓
  │         [8] create_calendar_events
  │          • Creates confirmed events in Google Calendar
  │          • Sets reminders (1 day email + 30 min popup)
  │          • Updates Slack message with status
  │          ↓
  │         END
  └─ NO → END
```

**Key Features:**
- **Stateful Execution**: Uses SQLite checkpointer for workflow persistence
- **Interruption Support**: Pauses at confirmation step waiting for Slack interactions
- **Background Processing**: FastAPI handles webhooks asynchronously to avoid timeouts

## Services

### Gmail Service (`services/gmail_service.py`)
- **Single Account Mode**: Fetches from one Gmail account
- **Multi-Account Mode**: Up to 3 accounts (set `GMAIL_MULTI_ACCOUNT=true`)
- **Features**:
  - OAuth 2.0 with automatic refresh
  - Base64 environment variable support for CI/CD
  - Time-range filtering (24h, 7d, 30d, etc.)
  - Message body decoding (plain text & HTML)
  - Email parsing: subject, from, to, date, body, labels

### AI Service (`services/ai_service.py`)
- **Model**: OpenAI GPT-4o with structured outputs
- **Functions**:
  1. **`classify_importance()`**: Categorizes emails
     - High: Job interviews, NYU announcements
     - Medium: Work/family emails
     - Low: Newsletters, promotions
  2. **`summarize_emails()`**: Structured daily summary
     - Overall overview
     - Job-related section
     - School-related section
     - Other important emails

### Calendar Service (`services/calendar_service.py`)
- **OAuth 2.0** authentication with base64 env var support
- **Event Creation**:
  - Timezone-aware (Asia/Taipei)
  - Auto reminders: 1 day email + 30 min popup
  - Extracts: title, start_time, end_time, location, description

### Event Service (`services/event_service.py`)
- **AI-Powered Detection**: GPT-4o with structured output
- **Confidence Scoring**:
  - 0.9-1.0: Explicit calendar invitations
  - 0.7-0.9: Activities with time & location
  - 0.5-0.7: Vague time information
  - <0.5: Not extracted
- **Filtering**: Only events with confidence ≥ 0.7

### Slack Service (`services/slack_service.py`)
- **Webhook Notifications**: Sends summary reports
- **Interactive Messages**: Button-based event confirmations
- **Features**:
  - Markdown → Slack mrkdwn conversion
  - Per-event action buttons (Confirm/Skip)
  - Real-time message updates with status

## Prerequisites

- Python 3.9 or higher
- Gmail account(s)
- OpenAI API key ([Get it here](https://platform.openai.com/api-keys))
- Slack workspace with webhook access
- Google Cloud project with Gmail & Calendar APIs enabled

## Installation

### 1. Clone Repository
```bash
git clone <your-repository-url>
cd email-summary-agent
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Gmail API

#### a. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing one
3. Enable **Gmail API** and **Google Calendar API**
4. Create OAuth 2.0 credentials (Desktop Application)
5. Download credentials JSON file

#### b. Single Account Setup
```bash
# Place credentials.json in project root
cp /path/to/downloaded/credentials.json credentials.json

# Run authorization flow (opens browser)
python services/gmail_service.py

# This generates token.json
```

#### c. Multi-Account Setup (Optional)
```bash
# Run multi-account authorization script
python authorize_accounts.py

# Follow prompts to authorize up to 3 accounts
# Generates: credentials_account1.json, token_account1.json, etc.
```

### 5. Set Up Google Calendar (Optional)

```bash
# Place calendar credentials in credentials/
mkdir -p credentials
cp /path/to/calendar_credentials.json credentials/calendar_credentials.json

# Run authorization flow
python init_calendar_credentials.py

# Select account (1, 2, or 3)
# Generates: credentials/calendar_token.json
```

### 6. Set Up Slack

#### a. Create Slack Webhook
1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Create new app → From scratch
3. Add "Incoming Webhooks" feature
4. Activate and create webhook for your channel
5. Copy webhook URL

#### b. Enable Interactive Components (for event confirmation)
1. In your Slack app settings → Interactivity & Shortcuts
2. Enable "Interactivity"
3. Set Request URL to: `https://your-domain.com/slack/interactive`
4. Save changes

#### c. Add Bot Token (for interactive messages)
1. OAuth & Permissions → Bot Token Scopes
2. Add `chat:write`, `channels:read`, `groups:read`
3. Install app to workspace
4. Copy "Bot User OAuth Token"

### 7. Configure Environment Variables

Create a `.env` file:

```env
# OpenAI API
OPENAI_API_KEY=sk-...

# Gmail Configuration
GMAIL_MULTI_ACCOUNT=false              # Set to 'true' for multi-account
GMAIL_CREDENTIALS_BASE64=...           # For deployment (see below)
GMAIL_TOKEN_BASE64=...

# OR for multi-account (if GMAIL_MULTI_ACCOUNT=true)
GMAIL_CREDENTIALS_ACCOUNT1_BASE64=...
GMAIL_TOKEN_ACCOUNT1_BASE64=...
GMAIL_CREDENTIALS_ACCOUNT2_BASE64=...
GMAIL_TOKEN_ACCOUNT2_BASE64=...
GMAIL_CREDENTIALS_ACCOUNT3_BASE64=...
GMAIL_TOKEN_ACCOUNT3_BASE64=...

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_BOT_TOKEN=xoxb-...               # For interactive messages
SLACK_SIGNING_SECRET=...               # For webhook verification
SLACK_CHANNEL_ID=C...                  # Target channel ID

# Google Calendar (Optional)
GOOGLE_CALENDAR_TOKEN_BASE64=...

# Email Settings
EMAIL_TIME_RANGE=24h                   # Options: 24h, 7d, 30d
MAX_EMAILS=20                          # Maximum emails to process

# LangSmith (Optional - for debugging)
LANGSMITH_API_KEY=...
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT=email-summary-agent
```

### 8. Encode Credentials for Deployment

For GitHub Actions or Render deployment:

```bash
# Run encoding script
python encode_credentials.py

# This outputs base64-encoded credentials
# Copy output to GitHub Secrets or Render environment variables
```

## Running Locally

### Option 1: Direct Execution
```bash
python main.py
```

### Option 2: FastAPI Server
```bash
# Development mode
uvicorn api.server:app --reload --port 8000

# Production mode
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

### Option 3: Trigger via API
```bash
# Health check
curl http://localhost:8000/health

# Trigger email summary
curl -X POST http://localhost:8000/webhook/email-summary
```

API documentation: Visit `http://localhost:8000/docs` for Swagger UI

## Deployment

### Option 1: GitHub Actions (Recommended - FREE)

GitHub Actions provides free scheduled execution (2000 minutes/month).

#### Setup Steps:

1. **Encode credentials** (if not already done):
```bash
python encode_credentials.py
```

2. **Add GitHub Secrets**:
   - Go to repository Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `OPENAI_API_KEY`
     - `GMAIL_CREDENTIALS_BASE64`
     - `GMAIL_TOKEN_BASE64`
     - (Or multi-account variants: `GMAIL_CREDENTIALS_ACCOUNT1_BASE64`, etc.)
     - `GOOGLE_CALENDAR_TOKEN_BASE64` (optional)
     - `SLACK_WEBHOOK_URL`
     - `SLACK_BOT_TOKEN`
     - `SLACK_SIGNING_SECRET`
     - `SLACK_CHANNEL_ID`
     - `RENDER_WEBHOOK_URL` (see below)
     - `EMAIL_TIME_RANGE` (optional, default: 24h)
     - `MAX_EMAILS` (optional, default: 20)

3. **Deploy FastAPI to Render** (for Slack webhooks):
   - Create free account on [Render](https://render.com/)
   - New Web Service → Connect GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.server:app --host 0.0.0.0 --port $PORT`
   - Add all environment variables from step 2
   - Copy the Render service URL

4. **Update GitHub Actions**:
   - Add `RENDER_WEBHOOK_URL` secret with value: `https://your-render-app.onrender.com/webhook/email-summary`

5. **Configure Schedule** (optional):
   - Edit `.github/workflows/email-summary.yml`
   - Modify cron schedule (default: UTC 00:00 = Taiwan 08:00)
   ```yaml
   schedule:
     - cron: '0 0 * * *'  # UTC time
   ```

6. **Push to GitHub**:
```bash
git add .
git commit -m "Setup GitHub Actions deployment"
git push origin main
```

#### Workflow Trigger:
- **Automatic**: Runs daily at scheduled time
- **Manual**: Go to Actions tab → "Daily Email Summary" → Run workflow

**Advantages:**
- Completely free (2000 minutes/month)
- No credit card required
- Automatic execution
- Easy to adjust schedule
- No server maintenance

### Option 2: Render Only (Alternative)

Deploy FastAPI directly on Render with scheduled jobs:

1. Create Web Service on Render
2. Add all environment variables
3. Use Render Cron Jobs (paid feature) or external cron service

### Option 3: Local Cron (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add line (example: daily at 9 AM)
0 9 * * * cd /path/to/email-summary-agent && /path/to/venv/bin/python main.py >> /tmp/email-summary.log 2>&1
```

## Authentication Mechanisms

### Gmail & Calendar OAuth 2.0
- **Flow Type**: Installed Application (Desktop)
- **Scopes**:
  - Gmail: `gmail.readonly`
  - Calendar: `calendar`
- **Token Storage**: Pickle format (binary)
- **Refresh**: Automatic when expired
- **Multi-Account**: Separate credential files per account

### Slack Signature Verification
- **Method**: HMAC-SHA256
- **Headers**: `x-slack-request-timestamp`, `x-slack-signature`
- **Purpose**: Ensure requests originate from Slack

### API Keys
- **OpenAI**: Bearer token in request headers
- **LangSmith**: Optional for debugging/tracing

## Multi-Account Support

Enable processing from multiple Gmail accounts:

1. **Set Environment Variable**:
```env
GMAIL_MULTI_ACCOUNT=true
```

2. **Authorize Accounts**:
```bash
python authorize_accounts.py
# Follow prompts for each account (1-3)
```

3. **Encode for Deployment**:
```bash
python encode_credentials.py
# Select multi-account option
```

4. **Set Deployment Variables**:
```env
GMAIL_CREDENTIALS_ACCOUNT1_BASE64=...
GMAIL_TOKEN_ACCOUNT1_BASE64=...
GMAIL_CREDENTIALS_ACCOUNT2_BASE64=...
GMAIL_TOKEN_ACCOUNT2_BASE64=...
# etc.
```

All accounts are processed in parallel and combined in the final report.

## Interactive Event Confirmation

When events are detected with confidence ≥ 0.7:

1. **Slack Message Posted** with:
   - Header: "檢測到行程/事件，請確認是否加入日曆"
   - Per-event blocks showing:
     - Event title
     - Time range
     - Location (if any)
   - Action buttons: "確認加入" / "跳過"

2. **User Clicks Button**:
   - Slack sends callback to `/slack/interactive`
   - Server verifies signature
   - Extracts event ID and action

3. **Workflow Resumes**:
   - Updates LangGraph state with confirmed events
   - Continues from `request_confirmation` node
   - Calls `create_calendar_events` with confirmed events

4. **Calendar Creation**:
   - Creates events in Google Calendar
   - Updates Slack message with status

## Configuration

### Email Time Range
Set `EMAIL_TIME_RANGE` to one of:
- `24h` (last 24 hours)
- `7d` (last 7 days)
- `30d` (last 30 days)
- Custom: `3d`, `14d`, etc.

### Max Emails
Set `MAX_EMAILS` to limit processing (default: 20)

### Cron Schedule Examples
```yaml
# Every day at 9 AM Taiwan time (UTC 1 AM)
cron: '0 1 * * *'

# Weekdays only at 8 AM Taiwan time (UTC 0 AM)
cron: '0 0 * * 1-5'

# Twice daily: 9 AM and 6 PM Taiwan time
# Use two separate cron entries
cron: '0 1 * * *'    # 9 AM
cron: '0 10 * * *'   # 6 PM
```

## Tech Stack

- **Agent Framework**: [LangGraph](https://github.com/langchain-ai/langgraph) - Stateful agent workflows
- **LLM**: [OpenAI GPT-4o](https://platform.openai.com/) - Classification & summarization
- **Email Service**: [Gmail API](https://developers.google.com/gmail/api) - Email fetching
- **Calendar Service**: [Google Calendar API](https://developers.google.com/calendar) - Event creation
- **Notification**: [Slack API](https://api.slack.com/) - Webhooks & interactive messages
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Webhook handling
- **Deployment**: [GitHub Actions](https://github.com/features/actions) + [Render](https://render.com/)
- **State Persistence**: SQLite (via LangGraph checkpointer)

## Development Notes

### API Quotas
- **Gmail API**: 250 quota units/user/second, 1,000,000,000 quota units/day
- **OpenAI API**: Pay-per-token, monitor usage in dashboard
- **Slack API**: No specific limits for webhooks

### Security Best Practices
- Never commit credentials or tokens to Git
- Use `.env` for local development
- Use GitHub Secrets/Render Env Vars for deployment
- Rotate API keys periodically
- Enable Slack signature verification

### Debugging
- Enable LangSmith tracing:
  ```env
  LANGSMITH_TRACING_V2=true
  LANGSMITH_API_KEY=...
  ```
- View traces at [smith.langchain.com](https://smith.langchain.com/)
- Check FastAPI logs on Render dashboard
- View GitHub Actions logs in repository

### Extending the System
- **Add more classification categories**: Modify prompts in `ai_service.py`
- **Change workflow**: Edit `agent/graph.py`
- **Add new notification channels**: Create new service in `services/`
- **Custom event detection rules**: Modify `event_service.py`

## Troubleshooting

### Issue: Gmail authentication fails
**Solution**:
- Re-run OAuth flow: `python services/gmail_service.py`
- Check credentials.json is valid
- Ensure Gmail API is enabled in Google Cloud Console

### Issue: Slack webhook returns 404
**Solution**:
- Verify webhook URL in Slack app settings
- Check URL is correctly set in environment variables
- Test with curl: `curl -X POST -H 'Content-Type: application/json' -d '{"text":"test"}' $SLACK_WEBHOOK_URL`

### Issue: Calendar events not created
**Solution**:
- Ensure `GOOGLE_CALENDAR_TOKEN_BASE64` is set
- Re-authorize: `python init_calendar_credentials.py`
- Check Calendar API is enabled
- Verify timezone settings in `calendar_service.py`

### Issue: GitHub Actions timeout
**Solution**:
- Actions triggers Render webhook and returns immediately
- Check Render logs for actual execution errors
- Ensure Render service is awake (free tier sleeps after inactivity)

### Issue: Interactive buttons don't work
**Solution**:
- Verify `SLACK_BOT_TOKEN` is set correctly
- Check Interactivity & Shortcuts is enabled in Slack app
- Ensure Request URL points to deployed server
- Validate `SLACK_SIGNING_SECRET` matches app settings

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- [OpenAI API](https://platform.openai.com/)
- [Google APIs](https://developers.google.com/)
- [Slack API](https://api.slack.com/)

---
