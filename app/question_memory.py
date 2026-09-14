import html
import json
import re
from datetime import datetime, timezone


ANSWERS_FILE = "candidate/application_answers.json"


def normalize_text(text: str) -> str:
    text = html.unescape(text or "")

    # Remove simple HTML tags.
    text = re.sub(r"<[^>]+>", " ", text)

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def load_question_memory() -> dict:
    try:
        with open(ANSWERS_FILE, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        return {
            "global": {},
            "companies": {}
        }


def save_question_memory(memory: dict):
    with open(ANSWERS_FILE, "w") as file:
        json.dump(
            memory,
            file,
            indent=2
        )


def canonicalize_question(
    question: dict
) -> tuple[str | None, str | None]:

    label = question.get("label", "")
    description = question.get("description", "")

    text = normalize_text(
        f"{label} {description}"
    )

    # Global facts

    if (
        "security clearance" in text
        and (
            "eligible" in text
            or "eligibility" in text
        )
    ):
        return (
            "security_clearance_eligibility",
            "global"
        )

    if (
        "clearance level" in text
        or (
            "held" in text
            and "security clearance" in text
            and "past" in text
        )
    ):
        return (
            "security_clearance_level",
            "global"
        )

    if (
        "protected individual" in text
        or "export controls" in text
        or "export control" in text
    ):
        return (
            "export_control_status",
            "global"
        )

    # Company-specific facts

    if (
        "previously applied" in text
        or "applied before" in text
        or "applied to" in text
    ):
        return (
            "previously_applied_to_company",
            "company"
        )

    if (
        "ever been employed" in text
        or "previously employed" in text
        or "worked at" in text
        or "worked for" in text
        or "prior employment" in text
        or "experience at" in text
    ):
        return (
            "previously_employed_by_company",
            "company"
        )

    if (
        "conflict of interest" in text
        or (
            "government" in text
            and "oversight" in text
        )
    ):
        return (
            "government_conflict_of_interest",
            "company"
        )

    if (
        "how did you hear" in text
        or "how did you learn about" in text
        or "how did you find" in text
    ):
        return (
            "how_heard_about_company",
            "company"
        )

    if (
        "deemed export license" in text
        or (
            re.search(r"\bear\b", text)
            and "export" in text
        )
    ):
        return (
            "deemed_export_license_eligibility",
            "global"
        )


    if (
        "contractual obligations" in text
        or (
            "agreements" in text
            and "interfere" in text
            and "ability to join" in text
        )
    ):
        return (
            "employment_restrictive_obligations",
            "global"
        )

    return None, None


def get_saved_answer(
    question: dict,
    company: str
):
    key, scope = canonicalize_question(
        question
    )

    if not key:
        return None

    memory = load_question_memory()

    if scope == "global":
        return memory.get(
            "global",
            {}
        ).get(key)

    company_key = company.lower().strip()

    return (
        memory
        .get("companies", {})
        .get(company_key, {})
        .get(key)
    )


def save_answer(
    question: dict,
    company: str,
    answer_label: str
):
    key, scope = canonicalize_question(
        question
    )

    if not key:
        return False

    memory = load_question_memory()

    record = {
        "answer": answer_label,
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "aliases": [
            normalize_text(
                question.get("label", "")
            )
        ]
    }

    if scope == "global":
        memory.setdefault(
            "global",
            {}
        )[key] = record

    else:
        company_key = company.lower().strip()

        company_memory = (
            memory
            .setdefault(
                "companies",
                {}
            )
            .setdefault(
                company_key,
                {}
            )
        )

        company_memory[key] = record

    save_question_memory(memory)

    return True