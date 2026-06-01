# Devin Automation

An event-driven automation system that uses the Devin API to autonomously 
remediate GitHub issues. When an issue is labeled `devin-fix` in the 
[superset-cognition](https://github.com/alissa-hs/superset-cognition) 
repository, this system automatically creates a Devin session to fix the 
issue and opens a pull request with the changes.

## Architecture

```
Issue labeled "devin-fix" in superset-cognition
  → dispatch.yml triggers in superset-cognition
    → repository_dispatch event fired to devin-automation
      → devin-fix.yml triggers in devin-automation
        → orchestrate.py runs
          → Devin API session created
            → Devin reads issue, makes fix, opens PR
              → Status comment posted back on issue
                → Session logged to observability/session_log.json
```

## Repositories

- **[devin-automation](https://github.com/alissa-hs/devin-automation)** — 
  this repo. Contains the GitHub Actions workflows, orchestrator script, 
  and Docker setup.
- **[superset-cognition](https://github.com/alissa-hs/superset-cognition)** — 
  the target repository. Contains the issues being remediated and the 
  dispatch workflow that triggers this automation.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- A Devin API key (`apk_user_` format)
- A GitHub Personal Access Token with `repo` scope

## GitHub Secrets Required

Add these secrets to both repositories under Settings → Secrets and variables → Actions:

| Secret | Description |
|--------|-------------|
| `DEVIN_API_KEY` | Your Devin API key |
| `GH_TOKEN` | GitHub Personal Access Token with repo scope |
| `DEVIN_ORG_ID` | Your Devin organization ID |

## How to Trigger the Automation

1. Go to [superset-cognition issues](https://github.com/alissa-hs/superset-cognition/issues)
2. Open any issue
3. Add the `devin-fix` label
4. The automation will trigger automatically:
   - `dispatch.yml` fires in superset-cognition
   - `devin-fix.yml` fires in devin-automation
   - Devin creates a session and begins working
   - A comment is posted on the issue when complete
   - A PR is opened in superset-cognition with the fix

## How to Run Locally with Docker

Create a `.env` file in the root of this repo:

```
DEVIN_API_KEY=your_api_key_here
GH_TOKEN=your_github_token_here
ISSUE_NUMBER=1
ISSUE_TITLE=Your issue title here
ISSUE_BODY=Your issue body here
ISSUE_URL=https://github.com/alissa-hs/superset-cognition/issues/1
REPO=alissa-hs/superset-cognition
```

Then run:

```bash
docker compose up
```

## Observability

Every session is logged to `observability/session_log.json` with the following information:

| Field | Description |
|-------|-------------|
| `timestamp` | When the session was triggered |
| `issue_number` | The GitHub issue number |
| `issue_title` | The issue title |
| `issue_url` | Link to the original issue |
| `session_id` | The Devin session ID |
| `session_url` | Link to the Devin session |
| `status` | success, error, or suspended |

Session status is also posted as a comment on the original GitHub issue, making it visible to anyone watching the issue without needing to check logs.

## How it Works

### Event Flow
1. A `devin-fix` label is added to an issue in superset-cognition
2. `dispatch.yml` catches the label event and fires a `repository_dispatch` 
   to devin-automation, forwarding the issue details as a payload
3. `devin-fix.yml` receives the dispatch and runs `orchestrate.py` inside 
   a Python environment with all secrets injected
4. `orchestrate.py` constructs a detailed prompt from the issue title and 
   body and creates a Devin session via the Devin API
5. The orchestrator polls the session every 30 seconds until Devin finishes
6. Once complete, a status comment is posted back on the original issue 
   with a link to the Devin session and any pull request opened
7. The session is recorded in `observability/session_log.json`
