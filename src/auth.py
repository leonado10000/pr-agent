import os
import time
import json
import jwt
import requests

def get_installation_access_token():
    """
    Generates an App JWT, uses it to find the repo's installation ID,
    and then exchanges it for a short-lived installation access token.
    This is a hardened, explicit authentication method.
    """
    app_id = os.environ['PR_AGENT_APP_ID']
    private_key_pem = os.environ['PR_AGENT_PRIVATE_KEY']
    
    try:
        github_context = json.loads(os.environ['GITHUB_CONTEXT'])
        repo_full_name = github_context['repository']
    except (KeyError, json.JSONDecodeError) as e:
        print(f"FATAL: Could not read repository name from GitHub context. Error: {e}")
        raise

    # 1. Generate the JSON Web Token (JWT)
    payload = {
        'iat': int(time.time()) - 60,
        'exp': int(time.time()) + (10 * 60) - 60,
        'iss': app_id
    }
    try:
        signed_jwt = jwt.encode(payload, private_key_pem, algorithm='RS256')
    except Exception as e:
        print(f"FATAL: Could not encode JWT. Check private key format. Error: {e}")
        raise

    # 2. Use the JWT to find the installation ID for the repository
    installation_url = f"https://api.github.com/repos/{repo_full_name}/installation"
    headers = {
        "Authorization": f"Bearer {signed_jwt}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(installation_url, headers=headers)
        response.raise_for_status()
        installation_id = response.json()['id']
        print(f"Successfully found installation ID for PR_AGENT: {installation_id}")
    except requests.exceptions.RequestException as e:
        print(f"FATAL: Could not get installation ID for repo '{repo_full_name}'.")
        print("ACTION REQUIRED: Ensure the 'PR_AGENT' App is installed on this repository.")
        print(f"Status: {e.response.status_code}, Body: {e.response.text}")
        raise

    # 3. Exchange the JWT for an Installation Access Token using the fetched ID
    token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    try:
        response = requests.post(token_url, headers=headers)
        response.raise_for_status()
        token_data = response.json()
        return token_data['token']
    except requests.exceptions.RequestException as e:
        print(f"FATAL: Could not get installation token. Status: {e.response.status_code}, Body: {e.response.text}")
        raise