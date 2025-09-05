import os
import openai
import google.generativeai as genai
import httpx

# --- Initialize BOTH clients at the module level ---

# 1. Google Gemini Client
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 2. OpenAI Client (with the definitive proxy fix)
# The correct keyword is 'proxy' (singular), set to None to disable.
client_openai = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    http_client=httpx.Client(proxy=None) # <-- THIS IS THE FIX
)

# --- Agent Functions ---

def _get_file_summary(file_diff: str) -> str:
    """
    (The "Map" Step) Uses OpenAI's GPT-4o mini for fast, cheap analysis.
    """
    system_prompt = "You are a code analysis bot. Summarize the changes in this diff file in a concise, technical, bullet-point format."
    
    try:
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": file_diff},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error summarizing file with GPT-4o mini: {e}"

def get_strategic_summary(file_summaries: list[str]) -> str:
    """
    (The "Reduce" Step) Uses Google's Gemini 1.5 Pro for powerful, high-level synthesis.
    """
    system_prompt = """
    You are a principal engineer reviewing a pull request. 
    You have received summaries of changes from your junior engineers for each file. 
    Your task is to synthesize these summaries into a single, high-level strategic overview. 
    Focus on the overall goal, the architectural impact, and any potential risks.
    Structure your output with the 'Three-Pillar Analysis': ## Summary, ## Rationale, and ## Consequence.
    """
    model = genai.GenerativeModel('gemini-1.5-pro', system_instruction=system_prompt)
    
    combined_summaries = "\n\n---\n\n".join(file_summaries)
    
    try:
        response = model.generate_content(f"Here are the file summaries:\n{combined_summaries}")
        if not response.parts:
            return "Error: Gemini Pro returned no content, possibly due to a safety block."
        return response.text
    except Exception as e:
        return f"Error generating strategic summary with Gemini Pro: {e}"