import requests


BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

TARGET_KEYWORDS = [
    "software engineer",
    "software developer",
    "backend engineer",
    "backend developer",
    "java engineer",
    "java developer",
]


def is_relevant_title(title: str) -> bool:
    title_lower = title.lower()

    return any(
        keyword in title_lower
        for keyword in TARGET_KEYWORDS
    )


def get_job_details(board_token: str, job_id: int) -> dict:
    url = f"{BASE_URL}/{board_token}/jobs/{job_id}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return response.json()


def collect_greenhouse_jobs(board_token: str) -> list[dict]:
    url = f"{BASE_URL}/{board_token}/jobs"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    jobs = []

    for job in data.get("jobs", []):
        title = job.get("title", "")

        if not is_relevant_title(title):
            continue

        job_id = job.get("id")
        details = get_job_details(board_token, job_id)

        jobs.append({
            "id": f"greenhouse-{job_id}",
            "title": details.get("title", ""),
            "company": "",
            "description": details.get("content", ""),
            "location": details.get("location", {}).get("name", ""),
            "remote": False,
            "salary_min": None,
            "salary_max": None,
            "sponsorship": None,
            "company_size": None,
            "required_skills": [],
            "preferred_skills": [],
            "apply_url": details.get("absolute_url"),
            "source": "greenhouse"
        })

    return jobs