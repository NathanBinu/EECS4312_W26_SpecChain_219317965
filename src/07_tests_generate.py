"""generates tests from specs"""

import json
import os
import time
import requests
from dotenv import load_dotenv

SPEC_PATH = "spec/spec_auto.md"
TESTS_OUT = "tests/tests_auto.json"

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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

            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != 0:
                content = content[start:end]

            return content

        except Exception as e:
            wait_time = 5 * (attempt + 1)
            print(f"Error: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    raise RuntimeError("Failed after multiple retries.")


def build_tests_prompt(spec_text):
    return f"""
You are a software requirements engineering assistant.

Generate exactly 20 validation tests from the following automated requirements specification.

Return valid JSON only in this exact format:

{{
  "tests": [
    {{
      "test_id": "TA1",
      "requirement_id": "RA1",
      "scenario": " ... ",
      "steps": [
        " ... ",
        " ... "
      ],
      "expected_result": " ... "
    }}
  ]
}}

Rules:
- Generate exactly 20 tests total.
- Create exactly 2 tests for each requirement RA1 through RA10.
- Use test IDs TA1 through TA20.
- requirement_id must match one of RA1 to RA10.
- Each test must include scenario, steps, and expected_result.
- Steps must be short, ordered, and executable.
- expected_result must be specific and testable.
- Return JSON only, with no explanation before or after.

Specification:
{spec_text}
""".strip()


def main():
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set. Put it in .env or export it before running the script.")

    spec_text = load_text(SPEC_PATH)
    print(f"Loaded automated specification from {SPEC_PATH}")

    messages = [
        {
            "role": "system",
            "content": "You are a careful requirements engineering assistant. Return valid JSON only."
        },
        {
            "role": "user",
            "content": build_tests_prompt(spec_text)
        }
    ]

    raw = call_groq(messages, api_key)
    parsed = json.loads(raw)

    save_json(parsed, TESTS_OUT)
    print(f"Saved automated tests to {TESTS_OUT}")


if __name__ == "__main__":
    main()