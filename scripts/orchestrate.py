import os
import time
import json
import requests

DEVIN_API_KEY = os.environ["DEVIN_API_KEY"]
GH_TOKEN = os.environ["GH_TOKEN"]

ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE = os.environ["ISSUE_TITLE"]
ISSUE_BODY = os.environ["ISSUE_BODY"]
ISSUE_URL = os.environ["ISSUE_URL"]
REPO = os.environ["REPO"]

DEVIN_BASE = "https://api.devin.ai/v1"
GH_BASE = "https://api.github.com"

DEVIN_HEADERS = {
    "Authorization": f"Bearer {DEVIN_API_KEY}",
    "Content-Type": "application/json"
}
GH_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def create_devin_session() -> tuple[str, str]:
    prompt = f"""
    You are working on the GitHub repository: https://github.com/{REPO}

    Please fix the following issue:

    Title: {ISSUE_TITLE}

    Description: {ISSUE_BODY}

    Issue URL: {ISSUE_URL}

    Instructions:
    - Clone the repository and make the necessary changes
    - Ensure your changes match the acceptance criteria in the issue
    - Open a pull request with your changes
    - The PR title should reference the issue titles
    """
    print(f"Creating Devin session for issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")
    
    response = requests.post(
        f"{DEVIN_BASE}/sessions",
        headers=DEVIN_HEADERS,
        json={"prompt": prompt}
    )
    response.raise_for_status()
    
    data = response.json()
    session_id = data["session_id"]
    session_url = data["url"]
    
    print(f"Session created: {session_id}")
    print(f"Session URL: {session_url}")
    
    return session_id, session_url
    

def poll_session(session_id) -> tuple[str, dict]:
    print(f"Polling session {session_id} for completion...")

    max_attempts = 60
    attempts = 0

    while attempts < max_attempts:
        try:
            response = requests.get(
            f"{DEVIN_BASE}/session/{session_id}",
            headers=DEVIN_HEADERS
            )
            response.raise_for_status()

            data = response.json()
            status = data.get("status")

            print(f"Session status: {status} (attempt {attempts + 1}/{max_attempts})")

            if status == "exit":
                print("Session completed successfully")
                return "success", data
            elif status == "error":
                print("Session encountered an error")
                return "error", data
            elif status == "suspended":
                print("Session was suspended")
                return "suspended", data
        
            print("Session still running, checking again in 30 seconds...")

        except requests.exceptions.RequestException as e:
            print(f"Polling error (will retry): {e}")
        
        time.sleep(30)
        attempts += 1

def post_github_comment(status, session_id, session_url):
    if status == "success":
        comment = f"""## Devin Fix Complete
        **Issue:** {ISSUE_TITLE}
        **Status:** {status}
        **Devin Session:** {session_url}
        **Session ID:** {session_id}

        Devin has completed work on this issue. Please review the pull request opened by Devin for the proposed changes.
    """
    else:
        comment = f"""## Devin Fix Failed
        **Issue:** {ISSUE_TITLE}
        **Status:** {status}
        **Devin Session:** {session_url}
        **Session ID:** {session_id}

        Devin was unable to complete this fix. Please review the logs for more detail.
    """
        
    print(f"Posting comment to issue #{ISSUE_NUMBER}")

    response = requests.post(
        f"{GH_BASE}/repos/{REPO}/issues/{ISSUE_NUMBER}/comments",
        headers=GH_HEADERS,
        json={"body": comment}
    )
    response.raise_for_status()
    print("Comment posted successfully")


def save_session_log(status, session_id, session_url):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "issue_number": ISSUE_NUMBER,
        "issue_title": ISSUE_TITLE,
        "issue_url": ISSUE_URL,
        "session_id": session_id,
        "session_url": session_url,
        "status": status
    }

    log_file = "observability/session_log.json"

    try: 
        with open(log_file, "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

    print(f"Session log saved to {log_file}")

def main():
    print(f"Starting Devin automation for issue #{ISSUE_NUMBER}")
    print(f"Repository: {REPO}")

    session_id, session_url = create_devin_session()
    status, data = poll_session(session_id)
    post_github_comment(status, session_id, session_url)
    save_session_log(status, session_id, session_url)

    print(f"Automation complete. Status: {status}")

if __name__ == "__main__":
    main()