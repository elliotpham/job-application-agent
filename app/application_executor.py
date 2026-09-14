import json

from app.application_tracker import (
    load_applications,
    STATUS_READY_TO_APPLY,
)


def get_ready_to_apply_jobs() -> list[dict]:
    applications = load_applications()

    ready_jobs = []

    for application in applications.values():
        if (
            application.get("status") == STATUS_READY_TO_APPLY
            and application.get("recommendation") == "APPLY"
        ):
            ready_jobs.append(application)

    # Highest match score first.
    ready_jobs.sort(
        key=lambda job: job.get("match_score", 0),
        reverse=True
    )

    return ready_jobs


def run_application_queue():
    jobs = get_ready_to_apply_jobs()

    print(
        f"\n===== APPLICATION QUEUE ({len(jobs)}) =====\n"
    )

    if not jobs:
        print("No jobs are ready to apply.")
        return

    for job in jobs:
        print(
            f"{job['match_score']}% | "
            f"{job['title']}"
        )

        print(
            f"{job['company']} | "
            f"{job['location']}"
        )

        print(
            f"Apply URL: {job['apply_url']}"
        )

        print()


if __name__ == "__main__":
    run_application_queue()