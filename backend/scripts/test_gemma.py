"""Quick test for a Gemma API key via Google AI Studio (Gemini API).

Usage:
    pip install google-generativeai
    python backend/scripts/test_gemma.py
"""
import os
import sys
from pathlib import Path

import dotenv
dotenv.load_dotenv(Path(__file__).resolve().parent.parent / ".env")

api_key = os.getenv("GEMMA_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("No GEMMA_API_KEY or GOOGLE_API_KEY found in backend/.env")
    sys.exit(1)

try:
    import google.generativeai as genai
except ImportError:
    print("Install the client first:  pip install google-generativeai")
    sys.exit(1)

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemma-4-9b-it")
response = model.generate_content("Say 'API key works' and nothing else.")
print(response.text.strip())
