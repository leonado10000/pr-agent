import os
import re
import json
import requests
from auth import get_installation_access_token
from agent import _get_file_summary, get_strategic_summary

def post_pr_comment(token: str, repo_full_name: str, pr_number: int, body: str):
    """Posts a comment to the specified pull request using the installation token."""
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": body}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Successfully posted comment to PR #{pr_number}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"FATAL: Failed to post comment. Status: {e.response.status_code}, Body: {e.response.text}")
        raise

def get_pr_diff(token: str, diff_url: str) -> str:
    """Fetches the raw diff text for the pull request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff" # Critical: ask for the diff format
    }
    try:
        response = requests.get(diff_url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"FATAL: Failed to fetch PR diff. Status: {e.response.status_code}, Body: {e.response.text}")
        raise


def parse_diff_into_files(full_diff: str) -> list[str]:
    """A simple parser to split a full diff into individual file diffs."""
    # The pattern looks for the 'diff --git a/...' line that starts each file's section
    file_diffs = re.split(r'(?=diff --git a/)', full_diff)
    return [diff.strip() for diff in file_diffs if diff.strip()]

def main():
    """Main entry point for the GitHub Action."""
    print("PR_AGENT analysis initiated.")
    try:
        github_context = json.loads(os.environ['GITHUB_CONTEXT'])
        repo_full_name = github_context['repository']
        pr_number = github_context['event']['pull_request']['number']
        diff_url = github_context['event']['pull_request']['diff_url']

        print("Authenticating as PR_AGENT...")
        access_token = get_installation_access_token()
        print("Authentication successful.")

        print("Fetching PR diff...")
        full_diff_text = get_pr_diff(access_token, diff_url)

        print("Parsing diff into individual files...")
        file_diffs = parse_diff_into_files(full_diff_text)
        print(f"Found {len(file_diffs)} changed files.")

        print("Generating file-level summaries (Map step)...")
        file_summaries = [_get_file_summary(diff) for diff in file_diffs]

        # The "Reduce" step: Create the final strategic overview.
        print("Generating strategic summary (Reduce step)...")
        final_summary = get_strategic_summary(file_summaries)
        
        print(f"Posting final summary to {repo_full_name} PR #{pr_number}...")
        post_pr_comment(access_token, repo_full_name, pr_number, final_summary)

        print("PR_AGENT analysis complete.")
    except Exception as e:
        print(f"An unhandled error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()