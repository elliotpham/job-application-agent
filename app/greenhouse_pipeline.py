import json
from datetime import datetime, timezone

import requests

from app.greenhouse_collector import collect_greenhouse_jobs
from app.job_normalizer import normalize_jobs
from app.matcher import calculate_match
from app.application_tracker import (
    record_job,
    get_job_status,
)


PROFILE_FILE = "candidate/profile.json"
COMPANIES_FILE = "config/greenhouse_companies.json"
RESULTS_FILE = "data/greenhouse_results.json"


def load_profile() -> dict:
    with open(PROFILE_FILE, "r") as file:
        return json.load(file)


def load_companies() -> list[dict]:
    with open(COMPANIES_FILE, "r") as file:
        return json.load(file)


def save_results(results: list[dict]):
    with open(RESULTS_FILE, "w") as file:
        json.dump(results, file, indent=2)


def run_greenhouse_pipeline() -> list[dict]:
    profile = load_profile()
    companies = load_companies()

    all_jobs = []

    for company in companies:
        if not company.get("enabled", True):
            continue

        board_token = company["board_token"]
        company_name = company["company_name"]

        print(f"Scanning {company_name}...")

        try:
            jobs = collect_greenhouse_jobs(
                board_token=board_token,
                company_name=company_name
            )

            print(
                f"  Found {len(jobs)} potentially relevant jobs"
            )

            all_jobs.extend(jobs)

        except requests.RequestException as exc:
            print(
                f"  Failed to collect {company_name}: {exc}"
            )

    normalized_jobs = normalize_jobs(all_jobs)

    results = []

    for job in normalized_jobs:
        match = calculate_match(job, profile)

        # Persist this job in our application history.
        record_job(
            job=job,
            recommendation=match["recommendation"],
            match_score=match["match_score"]
        )

        application_status = get_job_status(
            job["id"]
        )

        result = {
            "job_id": job.get("id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "work_arrangement": job.get(
                "work_arrangement"
            ),
            "minimum_years_experience": job.get(
                "minimum_years_experience"
            ),
            "apply_url": job.get("apply_url"),
            "application_status": application_status,
            "evaluated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            **match
        }

        results.append(result)

    results.sort(
        key=lambda result: result["match_score"],
        reverse=True
    )

    save_results(results)

    return results


if __name__ == "__main__":
    results = run_greenhouse_pipeline()

    print("\n===== REAL JOB RESULTS =====\n")

    if not results:
        print("No matching-location jobs found.")

    for result in results:
        print(
            f"{result['match_score']}% | "
            f"{result['recommendation']} | "
            f"{result['title']}"
        )

        print(
            f"{result['company']} | "
            f"{result['location']}"
        )

        if result.get("application_status") == "APPLIED":
            print("Status: Already applied")

        if result["hard_filter_failures"]:
            print(
                "Reason:",
                ", ".join(
                    result["hard_filter_failures"]
                )
            )
        
        if result.get("minimum_years_experience") is not None:
            print(
                "Experience required:",
                result["minimum_years_experience"],
                "years"
            )

        print()