import re

from app.question_memory import (
    get_saved_answer,
)

def normalize_label(label: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        (label or "").lower().strip()
    )


def resolve_question(
    question: dict,
    profile: dict,
    company: str
) -> dict:
    label = normalize_label(
        question.get("label", "")
    )

    fields = question.get("fields", [])

    if not fields:
        return {
            "status": "UNSUPPORTED",
            "answer": None,
        }

    field = fields[0]
    field_name = field.get("name")
    field_type = field.get("type")

    # Standard Greenhouse fields
    standard_answers = {
        "first_name": profile.get("first_name"),
        "last_name": profile.get("last_name"),
        "email": profile.get("email"),
        "phone": profile.get("phone"),
    }

    if field_name in standard_answers:
        answer = standard_answers[field_name]

        if answer:
            return {
                "status": "ANSWERED",
                "answer": answer,
            }

        return {
            "status": "NEEDS_INPUT",
            "answer": None,
        }

    # Optional fields we do not need to invent.
    if not question.get("required", False):
        if (
            "preferred first name" in label
            or label == "website"
            or label == "cover letter"
            or "if other" in label
        ):
            return {
                "status": "OPTIONAL_SKIP",
                "answer": None,
            }

    # LinkedIn
    if "linkedin profile" in label:
        linkedin = profile.get("linkedin_url")

        if linkedin:
            return {
                "status": "ANSWERED",
                "answer": linkedin,
            }

        return {
            "status": "OPTIONAL_SKIP"
            if not question.get("required")
            else "NEEDS_INPUT",
            "answer": None,
        }

    # Work authorization
    if (
        "work authorization" in label
        or "authorized to work in the united states" in label
    ):
        authorized = profile.get(
            "work_authorization",
            {}
        ).get(
            "authorized_to_work_in_us"
        )

        if authorized is True:
            return select_answer(
                field,
                "Yes"
            )

        if authorized is False:
            return select_answer(
                field,
                "No"
            )

    # Sponsorship
    if (
        "require sponsorship" in label
        or "sponsorship" in label
    ):
        sponsorship = profile.get(
            "work_authorization",
            {}
        ).get(
            "requires_sponsorship_now_or_future"
        )

        if sponsorship is True:
            return select_answer(
                field,
                "Yes"
            )

        if sponsorship is False:
            return select_answer(
                field,
                "No"
            )

    saved = get_saved_answer(
        question,
        company
    )

    if saved:
        saved_answer = saved.get("answer")

        if field_type == "multi_value_single_select":
            return select_answer(
                field,
                saved_answer
            )

        return {
            "status": "ANSWERED",
            "answer": saved_answer,
            "source": "question_memory",
        }

    # Do NOT guess these.
    manual_keywords = [
        "clearance",
        "export controls",
        "protected individual",
        "history with",
        "previously applied",
        "previously employed",
        "ever been employed",
        "conflict of interest",
        "government",
        "how did you hear",
    ]

    if any(
        keyword in label
        for keyword in manual_keywords
    ):
        return {
            "status": "NEEDS_INPUT",
            "answer": None,
        }

    return {
        "status": "NEEDS_INPUT",
        "answer": None,
    }


def select_answer(
    field: dict,
    desired_label: str
) -> dict:
    values = field.get("values", [])

    for option in values:
        if (
            option.get("label", "").strip().lower()
            == desired_label.lower()
        ):
            return {
                "status": "ANSWERED",
                "answer": option.get("value"),
                "answer_label": option.get("label"),
            }

    return {
        "status": "NEEDS_INPUT",
        "answer": None,
    }


def resolve_questions(
    questions: list[dict],
    profile: dict,
    company: str
) -> list[dict]:
    resolved = []

    for question in questions:
        resolution = resolve_question(
            question,
            profile,
            company
        )

        resolved.append({
            "label": question.get("label"),
            "required": question.get(
                "required",
                False
            ),
            "fields": question.get(
                "fields",
                []
            ),
            **resolution,
        })

    return resolved