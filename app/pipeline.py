import json
from datetime import datetime, timezone

from job_collector import collect_jobs
from matcher import calculate_match

from job_normalizer import normalize_jobs

RESULTS_FILE = "data/results.json"


def load_profile(filename: str = "candidate/profile.json") -> dict:
    """Load the candidate profile."""

    with open(filename, "r") as file:
        return json.load(file)


def save_results(results: list[dict]):
    """Save pipeline results to disk."""

    with open(RESULTS_FILE, "w") as file:
        json.dump(results, file, indent=2)


def run_pipeline():
    """Collect jobs and evaluate each one against the candidate profile."""

    profile = load_profile()
    raw_jobs = collect_jobs()
    jobs = normalize_jobs(raw_jobs)

    results = []

    for job in jobs:
        match = calculate_match(job, profile)

        result = {
            "job_id": job.get("id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            **match
        }

        results.append(result)

    save_results(results)

    return results


if __name__ == "__main__":
    results = run_pipeline()

    print("\n===== JOB MATCH RESULTS =====\n")

    for result in results:
        print(
            f"{result['title']} at {result['company']}"
        )
        print(
            f"Score: {result['match_score']}%"
        )
        print(
            f"Recommendation: {result['recommendation']}"
        )

        if result["hard_filter_failures"]:
            print(
                "Hard filters:",
                ", ".join(result["hard_filter_failures"])
            )

        print()