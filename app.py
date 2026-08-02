import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

RESPONSE_SCHEMA = {
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


def extract(doc_text: str) -> dict:
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
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
        ),
    )
    return json.loads(response.text)


# ---------- UI ----------

st.set_page_config(page_title="API Doc Analyzer", page_icon="🔍")
st.title("🔍 API Documentation Analyzer")
st.caption("Upload an API doc (.md or .txt) and extract structured integration details using Gemini.")

uploaded_file = st.file_uploader("Upload a documentation file", type=["md", "txt"])
pasted_text = st.text_area("...or paste documentation text here", height=200)

doc_text = None
if uploaded_file is not None:
    doc_text = uploaded_file.read().decode("utf-8")
elif pasted_text.strip():
    doc_text = pasted_text

if st.button("Extract", type="primary", disabled=doc_text is None):
    with st.spinner("Analyzing documentation..."):
        try:
            result = extract(doc_text)
            st.success("Extraction complete")

            st.subheader("Summary")
            col1, col2 = st.columns(2)
            col1.metric("Auth Type", result.get("auth_type", "Unknown"))
            col2.metric("Endpoints Found", len(result.get("endpoints", [])))

            st.subheader("Base URL")
            st.code(result.get("base_url") or "Not specified")

            st.subheader("Endpoints")
            for ep in result.get("endpoints", []):
                st.markdown(f"**{ep['method']}** `{ep['path']}` — {ep['description']}")

            st.subheader("Required Headers")
            st.write(result.get("required_headers", []))

            st.subheader("Rate Limit Info")
            st.write(result.get("rate_limit_info") or "Not specified")

            st.subheader("Notes")
            st.info(result.get("notes", ""))

            with st.expander("Raw JSON"):
                st.json(result)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
elif doc_text is None:
    st.info("Upload a file or paste text above to get started.")