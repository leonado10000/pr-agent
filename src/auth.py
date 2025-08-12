import os
import time
import json
import jwt
import requests

def get_installation_access_token():
    """Generates a JWT and exchanges it for a short-lived installation access token."""
    app_id = os.environ['PR_AGENT_APP_ID']
    private_key_pem = os.environ['PR_AGENT_PRIVATE_KEY']

    try:
        github_context = json.loads(os.environ['GITHUB_CONTEXT'])
        print(github_context['event'])
        installation_id = github_context['event']['installation']['id']
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing GitHub context for installation ID: {e}")
        raise

    # Generate the JSON Web Token (JWT), valid for 10 minutes
    payload = {
        'iat': int(time.time()) - 60,                # Issued at time (60s in the past to allow for clock drift)
        'exp': int(time.time()) + (10 * 60) - 60,    # Expiration time
        'iss': app_id                                # Issuer
    }

    try:
        signed_jwt = jwt.encode(payload, private_key_pem, algorithm='RS256')
    except Exception as e:
        print(f"FATAL: Could not encode JWT. Check private key format. Error: {e}")
        raise

    # Exchange the JWT for an Installation Access Token
    token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {signed_jwt}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.post(token_url, headers=headers)
        response.raise_for_status()
        token_data = response.json()
        return token_data['token']
    except requests.exceptions.RequestException as e:
        print(f"FATAL: Could not get installation token. Status: {e.response.status_code}, Body: {e.response.text}")
        raise