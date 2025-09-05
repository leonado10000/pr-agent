import os
import sys
import json
from unittest.mock import patch
from dotenv import load_dotenv

# --- ADD THIS BLOCK ---
# Add the 'src' directory to the Python path
# This allows our script to find the 'src.main' and other modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
# ----------------------

from main import main

# Load a .env file from the current directory
load_dotenv()

def run_local_test():
    """
    Simulates the GitHub Actions environment to run the main script locally.
    This makes a REAL call to the OpenAI API but mocks the GitHub API calls.
    """
    print("--- Starting Local Integration Test ---")

    # Load the sample diff file
    with open('tests\\65852.diff.txt', 'r') as f:
        sample_diff_text = f.read()

    # Mock the functions that interact with GitHub. We don't want to post comments.
    with patch('main.get_installation_access_token', return_value="dummy_github_token"), \
         patch('main.get_pr_diff', return_value=sample_diff_text), \
         patch('main.post_pr_comment') as mock_post_comment:

        # Set up the fake GitHub context
        os.environ['GITHUB_CONTEXT'] = json.dumps({
            'repository': 'your-username/pr-agent',
            'event': {
                'pull_request': {
                    'number': 123,
                    'diff_url': 'rahul jangra'
                }
            }
        })
        
        # Check if the key was loaded from the .env file
        if 'OPENAI_API_KEY' not in os.environ:
            print("FATAL: OPENAI_API_KEY not found. Ensure it's set in your .env file.")
            return

        # Run the main application logic
        main()

        # Assert that our comment function was called with the AI's output
        print("\n--- Test Assertions ---")
        mock_post_comment.assert_called_once()
        args, kwargs = mock_post_comment.call_args
        posted_summary = args[3] # The 'body' argument of post_pr_comment

        print(f"Verified that post_pr_comment was called.")
        print(f"Summary that would have been posted:\n---\n{posted_summary}\n---")

        assert len(posted_summary) > 20

if __name__ == '__main__':
    run_local_test()
