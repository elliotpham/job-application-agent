import requests
from app.job_extractor import (
    clean_job_description,
    extract_salary,
    extract_years_experience,
    extract_work_arrangement,
    extract_required_and_preferred_skills,
)

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
        description = clean_job_description(details.get("content", ""))
        salary_min, salary_max = extract_salary(description)
        years_experience = extract_years_experience(description)
        work_arrangement = extract_work_arrangement(description)
        required_skills, preferred_skills = (
            extract_required_and_preferred_skills(description)
        )

        jobs.append({
            "id": f"greenhouse-{job_id}",
            "title": details.get("title", "").strip(),
            "company": "",
            "description": description,
            "location": details.get("location", {}).get("name", ""),
            "remote": work_arrangement == "remote",
            "work_arrangement": work_arrangement,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "sponsorship": None,
            "company_size": None,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "minimum_years_experience": years_experience,
            "apply_url": details.get("absolute_url"),
            "source": "greenhouse"
        })

    return jobs