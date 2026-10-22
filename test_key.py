"""
Quick check of the Claude API connection used by the C24-IQ assistant.

Run it from the project folder (the one that contains app.py):
    python test_key.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag.rag_engine import call_anthropic_api, get_api_key, get_model

key = get_api_key()
print("API key found :", ("yes (starts with %s...)" % key[:7]) if key else "NO")
print("Model         :", get_model())

try:
    reply = call_anthropic_api(
        [{"role": "user", "content": "Reply with exactly one word: ready"}],
        "You are a connection test.",
    )
    text = "".join(b.get("text", "") for b in reply.get("content", []) if b.get("type") == "text")
    print("RESULT        : SUCCESS ->", text.strip())
except Exception as exc:
    print("RESULT        : FAILED  ->", exc)
    sys.exit(1)
