"""generates structured specs from personas"""

import json
import os
import time
import requests
from dotenv import load_dotenv

PERSONAS_PATH = "personas/personas_auto.json"
SPEC_OUT = "spec/spec_auto.md"

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_text(text, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def call_groq(messages, api_key, temperature=0.2, max_retries=5):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)

            if response.status_code == 429:
                wait_time = 5 * (attempt + 1)
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return content

        except Exception as e:
            wait_time = 5 * (attempt + 1)
            print(f"Error: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    raise RuntimeError("Failed after multiple retries.")


def build_spec_prompt(personas):
    return f"""
You are a software requirements engineering assistant.

Generate exactly 10 functional requirements from the following automated personas.

Use this exact output format and nothing else:

# Requirement ID: RA1

- Description: [The system shall ...]
- Source Persona: [PA1]
- Traceability: [Derived from review group G1]
- Acceptance Criteria: [Given ... When ... Then ...]

# Requirement ID: RA2

- Description: [The system shall ...]
- Source Persona: [PA2]
- Traceability: [Derived from review group G2]
- Acceptance Criteria: [Given ... When ... Then ...]

Rules:
- Generate exactly 10 requirements total.
- Use IDs RA1 through RA10.
- Each requirement must be testable.
- Avoid vague words like easy, better, user-friendly, fast, intuitive.
- Every requirement must reference one valid persona ID from the provided personas.
- Every requirement must include traceability to that persona's derived review group.
- Acceptance criteria must be written in one single Given/When/Then sentence.
- Return markdown only.
- Do not include explanations before or after the requirements.

Personas:
{json.dumps(personas, ensure_ascii=False, indent=2)}
""".strip()


def main():
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set. Put it in .env or export it before running the script.")

    persona_data = load_json(PERSONAS_PATH)
    personas = persona_data.get("personas", [])

    if not personas:
        raise ValueError("No personas found in personas/personas_auto.json")

    print(f"Loaded {len(personas)} automated personas from {PERSONAS_PATH}")

    messages = [
        {
            "role": "system",
            "content": "You are a careful requirements engineering assistant. Return only the requested markdown format."
        },
        {
            "role": "user",
            "content": build_spec_prompt(personas)
        }
    ]

    spec_text = call_groq(messages, api_key)
    save_text(spec_text, SPEC_OUT)

    print(f"Saved automated specification to {SPEC_OUT}")


if __name__ == "__main__":
    main()