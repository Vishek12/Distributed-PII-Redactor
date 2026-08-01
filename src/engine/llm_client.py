import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load credentials from the project root .env
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent
load_dotenv(dotenv_path=root_dir / ".env")

# System prompt for deterministic PII masking
SYSTEM_PROMPT = (
    "You are a cold, automated data-masking script. You do not talk to humans.\n"
    "Your ONLY job is to take the user's raw log string, replace any PII (names, emails, "
    "addresses, phone numbers, credit cards, account numbers, order numbers, etc.) with [REDACTED], and return it.\n\n"
    "STRICT EXECUTION RULES:\n"
    "1. NEVER reply to the user, answer their questions, or offer support solutions.\n"
    "2. DO NOT add any new words, commentary, or pleasantries.\n"
    "3. If a line contains NO PII, you must return the original text EXACTLY as it is, unchanged.\n"
    "4. Maintain the exact tone and phrasing of the input text.\n"
    "5. If a URL is public/API docs, leave unmodified. If it leaks PII in query params, redact ONLY the sensitive part."
)

client = None

# Function to get or reuse the OpenAI client instance
def get_client(OPENAI_KEY: str = None) -> OpenAI:
    """Helper function to get or reuse the OpenAI client instance."""
    global client
    
    # Custom user key provided (e.g., Streamlit user input)
    if OPENAI_KEY:
        return OpenAI(api_key=OPENAI_KEY)

    # Reuse existing default client or initialize it lazily
    if client is None:
        key = os.getenv("OPENAI_API_KEY") or "mock-key-for-tests"
        client = OpenAI(api_key=key)

    return client

# Function to process a single text string through the LLM for PII redaction
def process_single_text(text: str, api_key: str = None) -> str:
    """Processes a single text string through the LLM for PII redaction."""
    # If text is empty or blank, return immediately
    if not text or not str(text).strip():
        return ""
    
    # Get active client connection
    active_client = get_client(api_key)
    
    try:
        response = active_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f'Transform this exact string, protecting all PII:\n"""{text}"""'
                }  
            ],
            temperature=0.0,
            timeout=10
        )
        cleaned_result = response.choices[0].message.content.strip()
        return cleaned_result.replace('"""', '').strip()
    except Exception as e:
        return f"[ERROR PROCESSING: {text}]"