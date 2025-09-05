import os
import re
from openai import OpenAI
from dotenv import load_dotenv
# You'll need to pass the client around or initialize it as needed.
# For now, let's assume it's initialized.
load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def _get_file_summary(file_diff: str) -> str:
    """
    (The "Map" Step) Generates a high-density summary for a single file's diff.
    Uses a cheaper, faster model for this high-volume task.
    """
    system_prompt = "You are a code analysis bot. Summarize the changes in this diff file in a concise, technical, bullet-point format."
    
    # We use a cheaper model for this high-volume, parallelizable task.
    # This is a key architectural decision.
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Cheaper and faster
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": file_diff},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error summarizing file: {e}"

def get_strategic_summary(file_summaries: list[str]) -> str:
    """
    (The "Reduce" Step) Takes a list of file summaries and synthesizes a high-level overview.
    Uses our most powerful model for this critical reasoning task.
    """
    system_prompt = """
    You are a principal engineer reviewing a pull request. 
    You have received summaries of changes from your junior engineers for each file. 
    Your task is to synthesize these summaries into a single, high-level strategic overview. 
    Focus on the overall goal, the architectural impact, and any potential risks.
    Structure your output with the 'Three-Pillar Analysis': ## Summary, ## Rationale, and ## Consequence.
    """
    
    combined_summaries = "\n".join(file_summaries)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Our most powerful model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here are the file summaries:\n{combined_summaries}"},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating strategic summary: {e}"