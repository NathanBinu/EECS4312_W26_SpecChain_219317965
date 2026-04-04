"""automated persona generation pipeline"""
import json
import os
import time
import requests
from collections import defaultdict
from dotenv import load_dotenv

CLEAN_PATH = "data/reviews_clean.jsonl"
PROMPT_PATH = "prompts/prompt_auto.json"
GROUPS_OUT = "data/review_groups_auto.json"
PERSONAS_OUT = "personas/personas_auto.json"

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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

            # Extract JSON if the model adds extra text before or after it
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


def chunk_reviews_by_score(reviews, chunk_size=60):
    """
    Simple pre-grouping to avoid sending thousands of reviews at once.
    We bucket by score, then chunk each bucket.
    """
    buckets = defaultdict(list)
    for r in reviews:
        score = r.get("score", "unknown")
        buckets[score].append({
            "id": r["id"],
            "score": r.get("score"),
            "clean_text": r.get("clean_text", "")
        })

    chunks = []
    for score in sorted(buckets.keys()):
        bucket = buckets[score]
        for i in range(0, len(bucket), chunk_size):
            chunks.append(bucket[i:i + chunk_size])

    return chunks


def build_grouping_messages(prompt_text, review_chunk):
    return [
        {
            "role": "system",
            "content": "You are a careful requirements engineering assistant. Return valid JSON only."
        },
        {
            "role": "user",
            "content": (
                prompt_text
                + "\n\nReviews:\n"
                + json.dumps(review_chunk, ensure_ascii=False, indent=2)
            )
        }
    ]


def merge_group_candidates(group_candidates):
    """
    Merge similar groups from chunk-level LLM outputs into 5 final groups.
    This is a lightweight deterministic merge based on theme keywords.
    """
    theme_map = {
        "mood": "Mood tracking and self-reflection",
        "stress": "Mental health support and stress management",
        "anxiety": "Mental health support and stress management",
        "depression": "Mental health support and stress management",
        "insight": "Informational content and insights",
        "information": "Informational content and insights",
        "course": "Informational content and insights",
        "paid": "Pricing and paid feature limitations",
        "premium": "Pricing and paid feature limitations",
        "subscription": "Pricing and paid feature limitations",
        "privacy": "Privacy, trust, and data concerns",
        "data": "Privacy, trust, and data concerns",
        "tracking": "Privacy, trust, and data concerns"
    }

    final_groups = {
        "Mood tracking and self-reflection": {"review_ids": [], "example_reviews": []},
        "Mental health support and stress management": {"review_ids": [], "example_reviews": []},
        "Informational content and insights": {"review_ids": [], "example_reviews": []},
        "Pricing and paid feature limitations": {"review_ids": [], "example_reviews": []},
        "Privacy, trust, and data concerns": {"review_ids": [], "example_reviews": []}
    }

    for group in group_candidates:
        theme_text = (group.get("theme") or "").lower()
        matched_theme = None

        for keyword, canonical_theme in theme_map.items():
            if keyword in theme_text:
                matched_theme = canonical_theme
                break

        if matched_theme is None:
            matched_theme = "Informational content and insights"

        final_groups[matched_theme]["review_ids"].extend(group.get("review_ids", []))
        final_groups[matched_theme]["example_reviews"].extend(group.get("example_reviews", []))

    output = {"groups": []}
    idx = 1
    for theme, data in final_groups.items():
        unique_ids = []
        seen = set()
        for rid in data["review_ids"]:
            if rid not in seen:
                seen.add(rid)
                unique_ids.append(rid)

        unique_examples = []
        for ex in data["example_reviews"]:
            if ex not in unique_examples:
                unique_examples.append(ex)

        output["groups"].append({
            "group_id": f"G{idx}",
            "theme": theme,
            "review_ids": unique_ids[:25],
            "example_reviews": unique_examples[:2]
        })
        idx += 1
        # Adding warnings for groups with fewer than 10 review IDs
        for group in output["groups"]:
            if len(group["review_ids"]) < 10:
                print(f"Warning: {group['group_id']} has fewer than 10 review IDs.")

            if not group["example_reviews"]:
                group["example_reviews"] = [
                    f"Representative reviews for {group['theme']}.",
                    f"Grouped feedback related to {group['theme']}."
                ]

    return output

def rebalance_groups(output_groups):
    """
    If a group has fewer than 10 review IDs, borrow from the largest groups.
    This keeps all 5 groups non-empty and comparable.
    """
    groups = output_groups["groups"]

    def size(g):
        return len(g.get("review_ids", []))

    for group in groups:
        while size(group) < 10:
            donor = max(groups, key=size)
            if donor["group_id"] == group["group_id"] or size(donor) <= 10:
                break
            borrowed = donor["review_ids"].pop()
            if borrowed not in group["review_ids"]:
                group["review_ids"].append(borrowed)

    return output_groups

def generate_review_groups(reviews, prompt_config, api_key):
    chunks = chunk_reviews_by_score(reviews, chunk_size=60)
    group_candidates = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"Processing review chunk {i}/{len(chunks)} for grouping...")
        messages = build_grouping_messages(prompt_config["task_4_1_grouping_prompt"], chunk)
        raw = call_groq(messages, api_key)

        try:
            parsed = json.loads(raw)
            for g in parsed.get("groups", []):
                group_candidates.append(g)
        except json.JSONDecodeError:
            print(f"Warning: chunk {i} returned non-JSON output and was skipped.")

        # Delay added between chunk calls to reduce rate limiting
        time.sleep(3)

    final_groups = merge_group_candidates(group_candidates)
    final_groups = rebalance_groups(final_groups)
    final_groups = enforce_unique_ids_across_groups(final_groups)
    return final_groups

def enforce_unique_ids_across_groups(groups_output):
    seen = set()

    for group in groups_output["groups"]:
        unique_ids = []
        for rid in group["review_ids"]:
            if rid not in seen:
                unique_ids.append(rid)
                seen.add(rid)
        group["review_ids"] = unique_ids

    return groups_output

def build_persona_messages(prompt_text, groups):
    return [
        {
            "role": "system",
            "content": "You are a careful requirements engineering assistant. Return valid JSON only."
        },
        {
            "role": "user",
            "content": (
                prompt_text
                + "\n\nReview groups:\n"
                + json.dumps(groups, ensure_ascii=False, indent=2)
            )
        }
    ]


def generate_personas(groups, prompt_config, api_key):
    messages = build_persona_messages(prompt_config["task_4_2_persona_prompt"], groups)
    raw = call_groq(messages, api_key)

    try:
        parsed = json.loads(raw)
        return parsed
    except json.JSONDecodeError:
        raise ValueError("Groq persona generation returned invalid JSON.")


def main():
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set. Put it in .env or export it before running the script.")

    reviews = load_jsonl(CLEAN_PATH)
    prompt_config = load_json(PROMPT_PATH)

    print(f"Loaded {len(reviews)} cleaned reviews from {CLEAN_PATH}")

    # Step 4.1
    review_groups = generate_review_groups(reviews, prompt_config, api_key)
    save_json(review_groups, GROUPS_OUT)
    print(f"Saved automated review groups to {GROUPS_OUT}")

    # Step 4.2
    personas = generate_personas(review_groups, prompt_config, api_key)
    save_json(personas, PERSONAS_OUT)
    print(f"Saved automated personas to {PERSONAS_OUT}")


if __name__ == "__main__":
    main()