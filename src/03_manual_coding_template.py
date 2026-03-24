"""creates/updates coding table template + instructions"""

import json
from collections import Counter

CLEAN_PATH = "data/reviews_clean.jsonl"

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def print_sample_reviews(reviews, n=15):
    print(f"Loaded {len(reviews)} cleaned reviews from {CLEAN_PATH}\n")
    print(f"Showing first {n} cleaned reviews:\n")
    for r in reviews[:n]:
        print(f"ID: {r['id']}")
        print(f"Score: {r.get('score')}")
        print(f"Raw: {r.get('raw_text', '')}")
        print(f"Clean: {r.get('clean_text', '')}")
        print("-" * 80)

def print_score_distribution(reviews):
    scores = [r.get("score") for r in reviews if r.get("score") is not None]
    dist = Counter(scores)
    print("\nScore distribution:")
    for score in sorted(dist):
        print(f"{score} star: {dist[score]} reviews")

def search_reviews(reviews, keyword, limit=20):
    keyword = keyword.lower()
    matches = []
    for r in reviews:
        raw_text = (r.get("raw_text") or "").lower()
        clean_text = (r.get("clean_text") or "").lower()
        if keyword in raw_text or keyword in clean_text:
            matches.append(r)

    print(f"\nFound {len(matches)} reviews matching keyword: '{keyword}'\n")
    for r in matches[:limit]:
        print(f"ID: {r['id']}")
        print(f"Score: {r.get('score')}")
        print(f"Raw: {r.get('raw_text', '')}")
        print(f"Clean: {r.get('clean_text', '')}")
        print("-" * 80)

def main():
    reviews = load_jsonl(CLEAN_PATH)
    print_sample_reviews(reviews, n=15)
    print_score_distribution(reviews)

    while True:
        keyword = input("\nEnter a keyword to search reviews (or 'exit' to quit): ").strip()
        if keyword.lower() == "exit":
            break
        if keyword:
            search_reviews(reviews, keyword)

if __name__ == "__main__":
    main()