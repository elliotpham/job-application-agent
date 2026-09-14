import json

from app.application_question_resolver import resolve_questions
from app.greenhouse_form_inspector import get_application_questions


READY_STATUSES = {
    "ANSWERED",
    "ANSWERED_FILE",
    "OPTIONAL_SKIP",
}


def check_application_readiness(job: dict) -> dict:
    board_token = job.get("board_token")
    job_id = job.get("external_job_id")

    if not board_token or not job_id:
        return {
            "ready": False,
            "unresolved": [],
            "error": "Missing Greenhouse metadata",
        }

    data = get_application_questions(
        board_token,
        job_id
    )

    questions = data.get("questions", [])

    with open(
        "candidate/profile.json",
        "r"
    ) as file:
        profile = json.load(file)

    resolved = resolve_questions(
        questions,
        profile,
        job["company"]
    )

    unresolved = []

    for item in resolved:
        status = item.get("status")

        if status in READY_STATUSES:
            continue

        # Optional unresolved questions do not block submission.
        if not item.get("required", False):
            continue

        unresolved.append({
            "label": item.get("label"),
            "status": status,
        })

    return {
        "ready": len(unresolved) == 0,
        "unresolved": unresolved,
        "resolved_questions": resolved,
        "error": None,
    }

if __name__ == "__main__":
    from app.application_executor import get_ready_to_apply_jobs

    jobs = get_ready_to_apply_jobs()

    if not jobs:
        print("No jobs ready to apply.")
        raise SystemExit

    job = jobs[0]

    print("\n===== READINESS CHECK =====")
    print(job["title"])
    print(job["company"])

    result = check_application_readiness(
        job
    )

    print()
    print("Ready:", result["ready"])

    if result["error"]:
        print("Error:", result["error"])

    if result["unresolved"]:
        print("\nUnresolved required fields:")

        for item in result["unresolved"]:
            print(
                "-",
                item["label"],
                f"({item['status']})"
            )
    else:
        print(
            "\nAll required application fields are resolved."
        )