"""checks required files/folders exist"""

"""
00_validate_repo.py

Checks whether the repository contains the required folders and files.
Prints a clear validation report.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_FOLDERS = [
    "data",
    "personas",
    "spec",
    "tests",
    "metrics",
    "prompts",
    "src",
]

REQUIRED_FILES = [
    "data/reviews_clean.jsonl",
    "data/reviews_raw.jsonl",
    "data/review_groups_manual.json",
    "data/review_groups_auto.json",
    "data/review_groups_hybrid.json",
    "personas/personas_manual.json",
    "personas/personas_auto.json",
    "personas/personas_hybrid.json",
    "spec/spec_manual.md",
    "spec/spec_auto.md",
    "spec/spec_hybrid.md",
    "tests/tests_manual.json",
    "tests/tests_auto.json",
    "tests/tests_hybrid.json",
    "metrics/metrics_manual.json",
    "metrics/metrics_auto.json",
    "metrics/metrics_hybrid.json",
    "metrics/metrics_summary.json",
    "prompts/prompt_auto.json",
    "src/01_collect_or_import.py",
    "src/02_clean.py",
    "src/03_manual_coding_template.py",
    "src/05_personas_auto.py",
    "src/06_spec_generate.py",
    "src/07_tests_generate.py",
    "src/08_metrics.py",
    "src/run_all.py",
    "src/00_validate_repo.py",
]


def check_path(relative_path):
    full_path = os.path.join(ROOT, relative_path)
    return os.path.exists(full_path)


def main():
    print("Checking repository structure...")

    missing_items = []

    print("\nRequired folders:")
    for folder in REQUIRED_FOLDERS:
        if check_path(folder):
            print(f"{folder}/ found")
        else:
            print(f"{folder}/ MISSING")
            missing_items.append(folder + "/")

    print("\nRequired files:")
    for file_path in REQUIRED_FILES:
        if check_path(file_path):
            print(f"{file_path} found")
        else:
            print(f"{file_path} MISSING")
            missing_items.append(file_path)

    print()
    if missing_items:
        print("Repository validation incomplete")
        print("Missing items:")
        for item in missing_items:
            print(f"- {item}")
    else:
        print("Repository validation complete")


if __name__ == "__main__":
    main()