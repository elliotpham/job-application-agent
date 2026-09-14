import json

from app.application_executor import get_ready_to_apply_jobs
from app.application_question_resolver import resolve_questions
from app.greenhouse_form_inspector import get_application_questions


def build_submission_plan(job: dict) -> dict:
    board_token = job.get("board_token")
    job_id = job.get("external_job_id")

    if not board_token or not job_id:
        return {
            "ready": False,
            "actions": [],
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

    actions = []
    unresolved = []

    for question, resolution in zip(
        questions,
        resolved
    ):
        status = resolution.get("status")

        # Nothing needs to be filled.
        if status == "OPTIONAL_SKIP":
            continue

        # Required question still unresolved.
        if status not in {
            "ANSWERED",
            "ANSWERED_FILE",
        }:
            if question.get("required", False):
                unresolved.append({
                    "label": question.get("label"),
                    "status": status,
                })

            continue

        fields = question.get("fields", [])

        # File upload
        if status == "ANSWERED_FILE":
            file_field = next(
                (
                    field
                    for field in fields
                    if field.get("type") == "input_file"
                ),
                None
            )

            if not file_field:
                unresolved.append({
                    "label": question.get("label"),
                    "status": "FILE_FIELD_NOT_FOUND",
                })

                continue

            actions.append({
                "action": "upload_file",
                "label": question.get("label"),
                "field_name": file_field.get("name"),
                "file_path": resolution.get("answer"),
            })

            continue

        # Normal answered field
        if not fields:
            unresolved.append({
                "label": question.get("label"),
                "status": "FIELD_NOT_FOUND",
            })

            continue

        field = fields[0]

        field_type = field.get("type")

        if field_type == "multi_value_single_select":
            actions.append({
                "action": "select",
                "label": question.get("label"),
                "field_name": field.get("name"),
                "value": resolution.get("answer"),
                "value_label": resolution.get(
                    "answer_label"
                ),
            })

        else:
            if field.get("name") == "phone":
                phone_country = profile.get(
                    "phone_country",
                    "United States"
                )

                actions.append({
                    "action": "select_phone_country",
                    "label": "Phone Country",
                    "value": phone_country,
                })

            actions.append({
                "action": "fill",
                "label": question.get("label"),
                "field_name": field.get("name"),
                "value": resolution.get("answer"),
            })

    return {
        "ready": len(unresolved) == 0,
        "job_id": job.get("job_id"),
        "title": job.get("title"),
        "company": job.get("company"),
        "apply_url": job.get("apply_url"),
        "actions": actions,
        "unresolved": unresolved,
        "error": None,
    }


if __name__ == "__main__":
    jobs = get_ready_to_apply_jobs()

    if not jobs:
        print("No jobs ready to apply.")
        raise SystemExit

    job = jobs[0]

    plan = build_submission_plan(job)

    print("\n===== SUBMISSION PLAN =====\n")

    print(
        json.dumps(
            plan,
            indent=2
        )
    )