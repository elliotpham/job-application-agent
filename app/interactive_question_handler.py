import json

from app.application_executor import get_ready_to_apply_jobs
from app.application_question_resolver import resolve_questions
from app.greenhouse_form_inspector import get_application_questions
from app.question_memory import (
    canonicalize_question,
    save_answer,
)


def is_file_question(question: dict) -> bool:
    return any(
        field.get("type") == "input_file"
        for field in question.get("fields", [])
    )


def prompt_for_answer(question: dict) -> str | None:
    fields = question.get("fields", [])

    if not fields:
        return None

    field = fields[0]
    values = field.get("values", [])

    print("\n--------------------------------")
    print(question.get("label"))

    description = question.get("description")

    if description:
        print()
        print(description)

    # Multiple-choice question
    if values:
        print()

        for index, option in enumerate(values, start=1):
            print(
                f"{index}. {option.get('label')}"
            )

        while True:
            answer = input(
                "\nChoose an option number "
                "(or q to skip): "
            ).strip()

            if answer.lower() == "q":
                return None

            try:
                index = int(answer) - 1

                if 0 <= index < len(values):
                    return values[index]["label"]

            except ValueError:
                pass

            print("Invalid choice. Try again.")

    # Free-text question
    answer = input(
        "\nEnter your answer "
        "(or leave blank to skip): "
    ).strip()

    if not answer:
        return None

    return answer


def collect_unknown_answers(job: dict):
    board_token = job.get("board_token")
    job_id = job.get("external_job_id")

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

    print("\n===== APPLICATION =====")
    print(job["title"])
    print(job["company"])

    saved_count = 0

    for question, resolution in zip(
        questions,
        resolved
    ):
        if resolution["status"] != "NEEDS_INPUT":
            continue

        # Resume/file handling will be implemented separately.
        if is_file_question(question):
            print(
                "\nSkipping file field for now:",
                question.get("label")
            )
            continue

        canonical_key, scope = canonicalize_question(
            question
        )

        if canonical_key is None:
            print(
                "\nUnrecognized question type:"
            )
            print(question.get("label"))
            print(
                "This question is not saved automatically yet."
            )
            continue

        print(
            f"\nCanonical question: {canonical_key}"
        )

        answer_label = prompt_for_answer(
            question
        )

        if answer_label is None:
            continue

        saved = save_answer(
            question=question,
            company=job["company"],
            answer_label=answer_label
        )

        if saved:
            saved_count += 1

            print(
                f"Saved: {canonical_key} "
                f"→ {answer_label}"
            )

    print(
        f"\nSaved {saved_count} new answers."
    )

    # Resolve again to verify memory works.
    resolved_again = resolve_questions(
        questions,
        profile,
        job["company"]
    )

    remaining = [
        item
        for item in resolved_again
        if item["status"] == "NEEDS_INPUT"
        and not any(
            field.get("type") == "input_file"
            for field in item.get("fields", [])
        )
    ]

    print(
        f"Remaining unresolved questions: "
        f"{len(remaining)}"
    )


if __name__ == "__main__":
    jobs = get_ready_to_apply_jobs()

    if not jobs:
        print("No jobs ready to apply.")

    else:
        collect_unknown_answers(
            jobs[0]
        )