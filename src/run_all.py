"""runs the full pipeline end-to-end"""

"""
run_all.py

This script executes the automated pipeline from start to finish.

Order of execution:
1. Validate that the repository structure exists
2. Collect or import raw reviews -> data/reviews_raw.jsonl
3. Clean reviews -> data/reviews_clean.jsonl
4. Generate automated review groups -> data/review_groups_auto.json
5. Generate automated personas -> personas/personas_auto.json
6. Generate automated specification -> spec/spec_auto.md
7. Generate automated tests -> tests/tests_auto.json
8. Compute metrics for all available pipelines -> metrics/*.json

Notes:
- This script automates only the programmatic steps.
- Manual and hybrid artifacts are refined by hand and are not generated here.
- Make sure GROQ_API_KEY is available in your environment or .env file before running.
"""

import os
import sys
import subprocess


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "src")


def run_step(step_name, script_name):
    script_path = os.path.join(SRC_DIR, script_name)

    print("\n" + "=" * 70)
    print(f"Running: {step_name}")
    print(f"Script: {script_name}")
    print("=" * 70)

    result = subprocess.run([sys.executable, script_path], cwd=ROOT)

    if result.returncode != 0:
        print(f"\nERROR: {script_name} failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print(f"Completed: {step_name}")


def main():
    print("Starting full automated pipeline...")

    # Step 0: Validate repository structure first
    run_step("Repository validation", "00_validate_repo.py")

    # Step 1: Collect/import raw reviews
    run_step("Collect or import reviews", "01_collect_or_import.py")

    # Step 2: Clean reviews
    run_step("Clean reviews", "02_clean.py")

    # Step 3: Generate automated review groups and personas
    run_step("Generate automated review groups and personas", "05_personas_auto.py")

    # Step 4: Generate automated specification
    run_step("Generate automated specification", "06_spec_generate.py")

    # Step 5: Generate automated tests
    run_step("Generate automated tests", "07_tests_generate.py")

    # Step 6: Compute metrics
    run_step("Compute metrics", "08_metrics.py")

    print("\n" + "=" * 70)
    print("Automated pipeline finished successfully.")
    print("Produced files include:")
    print("- data/reviews_raw.jsonl")
    print("- data/reviews_clean.jsonl")
    print("- data/review_groups_auto.json")
    print("- personas/personas_auto.json")
    print("- spec/spec_auto.md")
    print("- tests/tests_auto.json")
    print("- metrics/metrics_auto.json")
    print("- metrics/metrics_summary.json")
    print("=" * 70)


if __name__ == "__main__":
    main()