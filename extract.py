import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Read the markdown doc
DOC_PATH = "sample_docs/razorpay_sample.md"
with open(DOC_PATH, "r", encoding="utf-8") as f:
    doc_text = f.read()

# 2. Define the schema we want Gemini to fill in
response_schema = {
    "type": "object",
    "properties": {
        "auth_type": {
            "type": "string",
            "enum": ["OAuth2", "API Key", "mTLS", "JWT", "Basic Auth", "None", "Unknown"],
        },
        "base_url": {"type": "string", "nullable": True},
        "endpoints": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "method": {"type": "string"},
                    "path": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["method", "path", "description"],
            },
        },
        "required_headers": {
            "type": "array",
            "items": {"type": "string"},
        },
        "rate_limit_info": {"type": "string", "nullable": True},
        "notes": {"type": "string"},
    },
    "required": ["auth_type", "base_url", "endpoints", "required_headers", "notes"],
}

# 3. Build the prompt
prompt = f"""You are analyzing API documentation to extract structured integration details.

Read the documentation below and extract the following:
- Authentication type used
- Base URL for the API
- List of endpoints (method, path, short description)
- Any required headers
- Rate limit information, if mentioned
- Notes: mention anything ambiguous, missing, or worth flagging for a developer integrating this API

If a field is not mentioned in the documentation, do not guess — use "Unknown" or null as appropriate.

DOCUMENTATION:
{doc_text}
"""

# 4. Call Gemini with structured output, low temperature
response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type="application/json",
        response_schema=response_schema,
    ),
)

# 5. Parse and validate
try:
    result = json.loads(response.text)
except json.JSONDecodeError as e:
    print("Failed to parse JSON:", e)
    print("Raw response:", response.text)
    exit(1)

# 6. Pretty-print
print(json.dumps(result, indent=2))