import json

import requests

from app.application_executor import get_ready_to_apply_jobs


BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


def get_application_questions(
    board_token: str,
    job_id: int
) -> dict:

    url = f"{BASE_URL}/{board_token}/jobs/{job_id}"

    response = requests.get(
        url,
        params={
            "questions": "true"
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def inspect_job(job: dict):
    board_token = job.get("board_token")
    job_id = job.get("external_job_id")

    if not board_token or not job_id:
        print("Missing Greenhouse metadata.")
        return

    data = get_application_questions(
        board_token,
        job_id
    )

    print("\n===== JOB =====")
    print(job["title"])
    print(job["company"])
    print()

    questions = data.get("questions", [])

    print(
        f"===== APPLICATION QUESTIONS ({len(questions)}) ====="
    )

    print(
        json.dumps(
            questions,
            indent=2
        )
    )


if __name__ == "__main__":
    jobs = get_ready_to_apply_jobs()

    if not jobs:
        print("No jobs ready to apply.")
    else:
        inspect_job(jobs[0])