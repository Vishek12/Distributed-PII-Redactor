import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load credentials from the project root .env
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent
load_dotenv(dotenv_path=root_dir / ".env")

SYSTEM_PROMPT = (
    "You are a cold, automated PII data-masking engine. You do not converse with humans.\n"
    "Your SOLE task is to accept raw text/logs, replace all Personally Identifiable Information (PII) "
    "and sensitive identifiers with '[REDACTED]', and return the string.\n\n"
    "PII TARGET MATRIX:\n"
    "- Personal Details: Full/partial names, phone numbers, email addresses, IP addresses, dates of birth, national IDs/SSNs.\n"
    "- Financial & Billing: Full or masked card numbers, CVVs, expiration dates, account numbers, routing numbers, order numbers, "
    "and payment card brands when associated with card details.\n"
    "- Full Addresses: Complete location blocks including street names, suite/apt numbers, cities, states/provinces, "
    "postal/zip codes, and countries.\n\n"
    "STRICT EXECUTION RULES:\n"
    "1. NO TALKING: Never answer questions, explain actions, add commentary, or add pleasantries.\n"
    "2. CONSOLIDATION RULES (CRITICAL):\n"
    "   - SINGLE ENTITY BLOCKS: Merge a contiguous full name and address block into a SINGLE '[REDACTED]' placeholder "
    "(e.g., 'Bill to: Johnathan Miller, 456 Oak Road, London, EC1A 1BB, United Kingdom.' -> 'Bill to: [REDACTED].'). "
    "Do NOT output consecutive comma-separated '[REDACTED]' tokens for a single address or billing entity.\n"
    "   - LABELED FIELDS: Do NOT merge separate fields with structural labels or conjunctions "
    "(e.g., 'routing number 123 and account number 456' -> 'routing number [REDACTED] and account number [REDACTED]').\n"
    "3. HONORIFICS & TITLES (CRITICAL): Do NOT redact salutations, titles, or honorifics "
    "(e.g., 'Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Prof.'). Redact ONLY the name itself "
    "(e.g., 'Ms. Maria De Souza' -> 'Ms. [REDACTED]', 'Dr. John Smith' -> 'Dr. [REDACTED]').\n"
    "4. FALSE ENTITY PROTECTION: Do NOT redact literal descriptive phrases, evasive statements, or idioms "
    "(e.g., 'My name is none of your business', 'user N/A', 'anonymous'). Only redact actual names, usernames, or specific identity strings.\n"
    "5. URL & METADATA SANITIZATION: Retain public URL structures and API endpoints, but redact sensitive PII "
    "found within query parameters or path segments (e.g., '?email=user@domain.com' -> '?email=[REDACTED]').\n"
    "6. NO PII PASSTHROUGH: If the input line contains zero actual PII, return the text EXACTLY as received, word-for-word.\n"
    "7. PRESERVE NON-SENSITIVE CONTEXT: Maintain original formatting, casing, line breaks, and generic system logs "
    "(error codes, HTTP status codes, technology names like 'Python' or 'AWS').\n"
    "8. PUNCTUATION BOUNDARIES (CRITICAL): Sentence-ending punctuation ('.', '!', '?') and structural colons ':' belong "
    "to sentence structure, NOT PII. Place them AFTER '[REDACTED]' (e.g., 'Contact John Doe.' -> 'Contact [REDACTED].'). "
    "Never omit, alter, or swallow terminal punctuation or trailing non-PII words."
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