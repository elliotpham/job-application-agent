from pathlib import Path


def get_resume_path(profile: dict) -> Path | None:
    resume_path = profile.get("resume_path")

    if not resume_path:
        return None

    return Path(resume_path)


def validate_resume(profile: dict) -> tuple[bool, str | None]:
    path = get_resume_path(profile)

    if path is None:
        return False, "No resume_path configured in candidate/profile.json"

    if not path.exists():
        return False, f"Resume file not found: {path}"

    if not path.is_file():
        return False, f"Resume path is not a file: {path}"

    allowed_extensions = {
        ".pdf",
        ".doc",
        ".docx",
        ".rtf",
        ".txt",
    }

    if path.suffix.lower() not in allowed_extensions:
        return (
            False,
            f"Unsupported resume file type: {path.suffix}"
        )

    return True, None


def resolve_resume(profile: dict) -> dict:
    valid, error = validate_resume(profile)

    if not valid:
        return {
            "status": "NEEDS_INPUT",
            "answer": None,
            "error": error,
        }

    path = get_resume_path(profile)

    return {
        "status": "ANSWERED_FILE",
        "answer": str(path),
    }