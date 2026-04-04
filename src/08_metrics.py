"""computes metrics: coverage/traceability/ambiguity/testability"""

import json
import os
import re

CLEAN_DATASET_PATH = "data/reviews_clean.jsonl"

MANUAL_GROUPS_PATH = "data/review_groups_manual.json"
AUTO_GROUPS_PATH = "data/review_groups_auto.json"
HYBRID_GROUPS_PATH = "data/review_groups_hybrid.json"

MANUAL_PERSONAS_PATH = "personas/personas_manual.json"
AUTO_PERSONAS_PATH = "personas/personas_auto.json"
HYBRID_PERSONAS_PATH = "personas/personas_hybrid.json"

MANUAL_SPEC_PATH = "spec/spec_manual.md"
AUTO_SPEC_PATH = "spec/spec_auto.md"
HYBRID_SPEC_PATH = "spec/spec_hybrid.md"

MANUAL_TESTS_PATH = "tests/tests_manual.json"
AUTO_TESTS_PATH = "tests/tests_auto.json"
HYBRID_TESTS_PATH = "tests/tests_hybrid.json"

MANUAL_METRICS_OUT = "metrics/metrics_manual.json"
AUTO_METRICS_OUT = "metrics/metrics_auto.json"
HYBRID_METRICS_OUT = "metrics/metrics_hybrid.json"
SUMMARY_METRICS_OUT = "metrics/metrics_summary.json"

AMBIGUOUS_WORDS = {
    "easy",
    "easily",
    "better",
    "fast",
    "faster",
    "user-friendly",
    "user friendly",
    "intuitive",
    "simple",
    "quick",
    "quickly",
    "efficient",
    "efficiently",
    "seamless",
    "smooth",
    "convenient",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_groups_list(groups_obj):
    if isinstance(groups_obj, dict):
        return groups_obj.get("groups", [])
    if isinstance(groups_obj, list):
        return groups_obj
    return []


def get_personas_list(personas_obj):
    if isinstance(personas_obj, dict):
        return personas_obj.get("personas", [])
    if isinstance(personas_obj, list):
        return personas_obj
    return []


def get_tests_list(tests_obj):
    if isinstance(tests_obj, dict):
        return tests_obj.get("tests", [])
    if isinstance(tests_obj, list):
        return tests_obj
    return []


def count_unique_review_ids(groups):
    review_ids = set()
    for group in groups:
        for rid in group.get("review_ids", []):
            review_ids.add(rid)
    return len(review_ids)


def parse_spec_requirements(spec_text):
    """
    Parses specs in either of these formats:

    Bracketed:
    # Requirement ID: RM1
    - Description: [ ... ]
    - Source Persona: [PM-01]
    - Traceability: [Derived from review group G1]
    - Acceptance Criteria: [Given ... When ... Then ...]

    Non-bracketed:
    # Requirement ID: RA1
    - Description: The system shall ...
    - Source Persona: PA1
    - Traceability: Derived from review group G1
    - Acceptance Criteria: Given ... When ... Then ...
    """
    block_pattern = re.compile(
        r"# Requirement ID:\s*(?P<req_id>[A-Z]{2}\d+)\s*(?P<body>.*?)(?=(?:# Requirement ID:)|\Z)",
        re.DOTALL,
    )

    requirements = []

    for match in block_pattern.finditer(spec_text):
        req_id = match.group("req_id").strip()
        body = match.group("body")

        def extract_field(field_name):
            # first try bracketed form
            m = re.search(
                rf"- {re.escape(field_name)}:\s*\[(.*?)\]",
                body,
                re.DOTALL
            )
            if m:
                return m.group(1).strip()

            m = re.search(
                rf"- {re.escape(field_name)}:\s*(.+)",
                body
            )
            if m:
                return m.group(1).strip()

            return ""

        requirements.append(
            {
                "requirement_id": req_id,
                "description": extract_field("Description"),
                "source_persona": extract_field("Source Persona"),
                "traceability": extract_field("Traceability"),
                "acceptance_criteria": extract_field("Acceptance Criteria"),
            }
        )

    return requirements

def count_traceability_links(groups, personas, requirements, tests):
    """
    Count explicit traceable relationships between artifacts:
    - group -> persona if persona has derived_from_group
    - persona -> requirement if requirement Source Persona matches a persona id
    - requirement -> test if test requirement_id matches a requirement id
    """
    group_ids = {g.get("group_id") for g in groups if g.get("group_id")}
    persona_ids = set()
    group_to_persona_links = 0

    for p in personas:
        pid = p.get("id") or p.get("persona_id")
        if pid:
            persona_ids.add(pid)

        derived = p.get("derived_from_group")
        if derived in group_ids:
            group_to_persona_links += 1

    requirement_ids = set()
    persona_to_requirement_links = 0
    for r in requirements:
        rid = r.get("requirement_id")
        if rid:
            requirement_ids.add(rid)

        if r.get("source_persona") in persona_ids:
            persona_to_requirement_links += 1

    requirement_to_test_links = 0
    for t in tests:
        if t.get("requirement_id") in requirement_ids:
            requirement_to_test_links += 1

    return group_to_persona_links + persona_to_requirement_links + requirement_to_test_links


def compute_traceability_ratio(requirements, personas):
    if not requirements:
        return 0.0

    persona_ids = {
        (p.get("id") or p.get("persona_id"))
        for p in personas
        if (p.get("id") or p.get("persona_id"))
    }

    traced = 0
    for r in requirements:
        if r.get("source_persona") in persona_ids:
            traced += 1

    return round(traced / len(requirements), 4)


def compute_testability_rate(requirements, tests):
    if not requirements:
        return 0.0

    tested_req_ids = {t.get("requirement_id") for t in tests if t.get("requirement_id")}
    linked = sum(1 for r in requirements if r.get("requirement_id") in tested_req_ids)
    return round(linked / len(requirements), 4)


def compute_ambiguity_ratio(requirements):
    if not requirements:
        return 0.0

    ambiguous_count = 0
    for r in requirements:
        text = f"{r.get('description', '')} {r.get('acceptance_criteria', '')}".lower()
        if any(word in text for word in AMBIGUOUS_WORDS):
            ambiguous_count += 1

    return round(ambiguous_count / len(requirements), 4)


def compute_pipeline_metrics(groups_path, personas_path, spec_path, tests_path):
    reviews = load_jsonl(CLEAN_DATASET_PATH)
    groups_obj = load_json(groups_path)
    personas_obj = load_json(personas_path)
    tests_obj = load_json(tests_path)

    with open(spec_path, "r", encoding="utf-8") as f:
        spec_text = f.read()

    groups = get_groups_list(groups_obj)
    personas = get_personas_list(personas_obj)
    tests = get_tests_list(tests_obj)
    requirements = parse_spec_requirements(spec_text)

    dataset_size = len(reviews)
    persona_count = len(personas)
    requirements_count = len(requirements)
    tests_count = len(tests)
    traceability_links = count_traceability_links(groups, personas, requirements, tests)

    covered_review_count = count_unique_review_ids(groups)
    review_coverage_ratio = round(covered_review_count / dataset_size, 4) if dataset_size else 0.0
    traceability_ratio = compute_traceability_ratio(requirements, personas)
    testability_rate = compute_testability_rate(requirements, tests)
    ambiguity_ratio = compute_ambiguity_ratio(requirements)

    return {
        "dataset_size": dataset_size,
        "persona_count": persona_count,
        "requirements_count": requirements_count,
        "tests_count": tests_count,
        "traceability_links": traceability_links,
        "review_coverage_ratio": review_coverage_ratio,
        "traceability_ratio": traceability_ratio,
        "testability_rate": testability_rate,
        "ambiguity_ratio": ambiguity_ratio,
    }


def try_compute_pipeline(name, groups_path, personas_path, spec_path, tests_path, out_path):
    required_paths = [groups_path, personas_path, spec_path, tests_path, CLEAN_DATASET_PATH]
    if not all(os.path.exists(p) for p in required_paths):
        print(f"Skipping {name}: missing one or more required files.")
        return None

    metrics = compute_pipeline_metrics(groups_path, personas_path, spec_path, tests_path)
    save_json(metrics, out_path)
    print(f"Saved {name} metrics to {out_path}")
    return metrics


def main():
    os.makedirs("metrics", exist_ok=True)

    summary = {}

    manual = try_compute_pipeline(
        "manual",
        MANUAL_GROUPS_PATH,
        MANUAL_PERSONAS_PATH,
        MANUAL_SPEC_PATH,
        MANUAL_TESTS_PATH,
        MANUAL_METRICS_OUT,
    )
    if manual is not None:
        summary["manual"] = manual

    auto = try_compute_pipeline(
        "auto",
        AUTO_GROUPS_PATH,
        AUTO_PERSONAS_PATH,
        AUTO_SPEC_PATH,
        AUTO_TESTS_PATH,
        AUTO_METRICS_OUT,
    )
    if auto is not None:
        summary["auto"] = auto

    hybrid = try_compute_pipeline(
        "hybrid",
        HYBRID_GROUPS_PATH,
        HYBRID_PERSONAS_PATH,
        HYBRID_SPEC_PATH,
        HYBRID_TESTS_PATH,
        HYBRID_METRICS_OUT,
    )
    if hybrid is not None:
        summary["hybrid"] = hybrid

    save_json(summary, SUMMARY_METRICS_OUT)
    print(f"Saved summary metrics to {SUMMARY_METRICS_OUT}")


if __name__ == "__main__":
    main()