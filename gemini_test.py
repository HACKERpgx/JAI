import os
import sys
import google.generativeai as genai

GEMINI_API_KEY = "MY_API_KEY"

def main() -> int:
    key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    if not key or key == "MY_API_KEY":
        print("Set GEMINI_API_KEY env var or replace GEMINI_API_KEY in gemini_test.py with your actual key.")
        return 2

    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = "Respond with exactly: JAI Gemini test OK"
        resp = model.generate_content(prompt)
        text = getattr(resp, "text", None)
        if not text and getattr(resp, "candidates", None):
            try:
                text = resp.candidates[0].content.parts[0].text
            except Exception:
                text = None
        if not isinstance(text, str):
            print("No text response received from Gemini.")
            return 3
        print(text.strip())
        return 0
    except Exception as e:
        print(f"Gemini request failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
