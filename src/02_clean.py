"""cleans raw data & make clean dataset"""

import json
import os
import re
import string
import emoji
import inflect
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

RAW_INPUT = "data/reviews_raw.jsonl"
CLEAN_OUTPUT = "data/reviews_clean.jsonl"

p = inflect.engine()
stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def save_jsonl(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def convert_numbers_to_text(text):
    def replacer(match):
        try:
            return p.number_to_words(match.group())
        except Exception:
            return match.group()
    return re.sub(r"\d+", replacer, text)

def clean_text(text):
    if not text:
        return ""

    text = emoji.replace_emoji(text, replace="")
    text = convert_numbers_to_text(text)
    text = text.lower()
    text = text.replace("\n", " ").replace("\r", " ")
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = []
    for token in text.split():
        if token in stop_words:
            continue
        tokens.append(lemmatizer.lemmatize(token))

    return " ".join(tokens)

def is_too_short(text, min_words=3):
    return len(text.split()) < min_words

def main():
    if not os.path.exists(RAW_INPUT):
        raise FileNotFoundError(f"{RAW_INPUT} does not exist. Run src/01_collect_reviews.py first.")

    raw_reviews = load_jsonl(RAW_INPUT)

    cleaned_reviews = []
    seen_texts = set()

    for review in raw_reviews:
        original_text = (review.get("content") or "").strip()

        if not original_text:
            continue

        cleaned_text = clean_text(original_text)

        if not cleaned_text:
            continue

        if is_too_short(cleaned_text):
            continue

        if cleaned_text in seen_texts:
            continue

        seen_texts.add(cleaned_text)

        cleaned_reviews.append({
            "id": review["id"],
            "reviewId": review.get("reviewId"),
            "app_name": review.get("app_name"),
            "score": review.get("score"),
            "raw_text": original_text,
            "clean_text": cleaned_text,
            "at": review.get("at")
        })

    save_jsonl(cleaned_reviews, CLEAN_OUTPUT)

    print(f"Raw reviews loaded: {len(raw_reviews)}")
    print(f"Cleaned reviews saved: {len(cleaned_reviews)}")
    print(f"Saved cleaned dataset to {CLEAN_OUTPUT}")

if __name__ == "__main__":
    main()