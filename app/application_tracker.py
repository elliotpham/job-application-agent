import json
import os
from datetime import datetime, timezone


APPLICATIONS_FILE = "data/applications.json"

STATUS_DISCOVERED = "DISCOVERED"
STATUS_READY_TO_APPLY = "READY_TO_APPLY"
STATUS_APPLIED = "APPLIED"
STATUS_FAILED = "FAILED"
STATUS_NEEDS_INPUT = "NEEDS_INPUT"

def load_applications() -> dict:
    if not os.path.exists(APPLICATIONS_FILE):
        return {}

    with open(APPLICATIONS_FILE, "r") as file:
        return json.load(file)


def save_applications(applications: dict):
    with open(APPLICATIONS_FILE, "w") as file:
        json.dump(applications, file, indent=2)


def get_application(job_id: str) -> dict | None:
    applications = load_applications()
    return applications.get(job_id)


def has_already_applied(job_id: str) -> bool:
    application = get_application(job_id)

    if not application:
        return False

    return application.get("status") == "APPLIED"


def record_job(
    job: dict,
    recommendation: str,
    match_score: int
):
    applications = load_applications()

    job_id = job["id"]

    now = datetime.now(
        timezone.utc
    ).isoformat()

    existing = applications.get(job_id)

    if existing:
        existing["last_seen_at"] = now
        existing["match_score"] = match_score
        existing["recommendation"] = recommendation

    else:
        applications[job_id] = {
            "job_id": job_id,
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "apply_url": job.get("apply_url"),
            "match_score": match_score,
            "recommendation": recommendation,
            "status": STATUS_DISCOVERED,
            "first_seen_at": now,
            "last_seen_at": now,
            "applied_at": None
        }

    save_applications(applications)


def mark_applied(job_id: str):
    applications = load_applications()

    if job_id not in applications:
        return

    applications[job_id]["status"] = STATUS_APPLIED
    applications[job_id]["applied_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    save_applications(applications)

def get_job_status(job_id: str) -> str | None:
    application = get_application(job_id)

    if not application:
        return None

    return application.get("status")

def mark_ready_to_apply(job_id: str):
    applications = load_applications()

    if job_id not in applications:
        return

    applications[job_id]["status"] = STATUS_READY_TO_APPLY
    save_applications(applications)


def mark_needs_input(job_id: str):
    applications = load_applications()

    if job_id not in applications:
        return

    applications[job_id]["status"] = STATUS_NEEDS_INPUT
    save_applications(applications)


def mark_failed(job_id: str):
    applications = load_applications()

    if job_id not in applications:
        return

    applications[job_id]["status"] = STATUS_FAILED
    save_applications(applications)