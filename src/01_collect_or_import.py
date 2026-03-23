"""imports or reads your raw dataset; if you scraped, include scraper here"""
import json
import os
from datetime import datetime
from google_play_scraper import reviews, Sort

# MindDoc Google Play package id
APP_ID = "de.moodpath.android"
APP_NAME = "MindDoc: Your Companion"

RAW_OUTPUT = "data/reviews_raw.jsonl"
METADATA_OUTPUT = "data/dataset_metadata.json"

TARGET_REVIEW_COUNT = 3000   # We can vary this based on how many reviews we decide to collect
LANG = "en"
COUNTRY = "ca"

def save_jsonl(records, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def collect_reviews(app_id, target_count=2000, lang="en", country="ca"):
    collected = []
    continuation_token = None

    while len(collected) < target_count:
        batch, continuation_token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=min(200, target_count - len(collected)),
            continuation_token=continuation_token
        )

        if not batch:
            break

        for i, review in enumerate(batch, start=1):
            collected.append({
                "id": f"minddoc_{len(collected) + 1}",
                "app_name": APP_NAME,
                "app_id": app_id,
                "reviewId": review.get("reviewId"),
                "userName": review.get("userName"),
                "score": review.get("score"),
                "content": review.get("content"),
                "thumbsUpCount": review.get("thumbsUpCount"),
                "reviewCreatedVersion": review.get("reviewCreatedVersion"),
                "at": review.get("at").isoformat() if review.get("at") else None,
                "replyContent": review.get("replyContent"),
                "repliedAt": review.get("repliedAt").isoformat() if review.get("repliedAt") else None
            })

        if continuation_token is None:
            break

    return collected

def save_metadata(raw_count, path):
    metadata = {
        "app_name": APP_NAME,
        "app_id": APP_ID,
        "dataset_size_raw": raw_count,
        "collection_method": "Collected from Google Play using the google-play-scraper Python package",
        "collection_date": datetime.now().isoformat(),
        "cleaning_decisions": [
            "Removed duplicate reviews",
            "Removed empty reviews",
            "Removed extremely short reviews",
            "Removed punctuation",
            "Removed special characters and emojis",
            "Converted numbers to text",
            "Removed extra whitespace",
            "Converted all text to lowercase",
            "Removed stop words",
            "Lemmatized words"
        ],
        "notes": "3000 raw reviews were successfully collected from Google Play. After preprocessing and cleaning (removal of duplicates, empty entries, and low-quality reviews), the final cleaned dataset contains 2585 reviews."
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    records = collect_reviews(APP_ID, TARGET_REVIEW_COUNT, LANG, COUNTRY)
    save_jsonl(records, RAW_OUTPUT)
    save_metadata(len(records), METADATA_OUTPUT)

    print(f"Collected {len(records)} reviews.")
    print(f"Saved raw data to {RAW_OUTPUT}")
    print(f"Saved metadata to {METADATA_OUTPUT}")