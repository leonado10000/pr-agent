# In src/agent.py

import os
from openai import OpenAI # Or whatever provider you're using

def summarize_diff(diff_text: str) -> str:
    """
    Generates a summary for a given diff text using a simple, direct prompt.
    This is our "dumb" agent.
    """
    # A simple hack for now: if the diff is too large, truncate it.
    # Phase 3 will solve this properly.
    if len(diff_text) > 15000: # Approx 4k tokens
        diff_text = diff_text[:15000] + "\n\n... (diff truncated)"

    # You'll need to set OPENAI_API_KEY as a new secret in your repo
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    system_prompt = "You are an expert code reviewer. Your purpose is to provide a concise, high-level summary of a pull request based on its diff. Focus on the 'what' and 'why', not the line-by-line changes."
    
    human_prompt = f"""
    Please provide a summary for the following code changes:
    
    ```diff
    {diff_text}
    ```
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Or another fast, capable model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return "Error: Could not generate a summary for the diff."