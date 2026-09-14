import requests
from app.job_extractor import (
    clean_job_description,
    extract_salary,
    extract_years_experience,
    extract_work_arrangement,
    extract_required_and_preferred_skills,
)
from app.location_utils import (
    is_washington_state_location,
    is_us_remote_location,
    location_indicates_remote,
)
from app.job_extractor import (
    clean_job_description,
    extract_salary,
    extract_years_experience,
    extract_work_arrangement,
    extract_required_and_preferred_skills,
    extract_sponsorship,
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

EXCLUDED_TITLE_KEYWORDS = [
    # Wrong seniority
    "intern",
    "internship",
    "early career",
    "new grad",
    "graduate",
    "junior",
    "staff",
    "principal",
    "lead software",
    "manager",
    "director",

    # Wrong specialization
    "front end",
    "frontend",
    "front-end",
    "embedded",
    "firmware",
    "test automation",
    "qa engineer",
    "quality assurance",
    "data science",
    "data scientist",
    "robotics",
    "sensor fusion",
    "computer vision",
    "ios",
    "android",
    "mobile engineer",
    "rust software",
]


def is_relevant_title(title: str) -> bool:
    title_lower = title.lower().strip()

    if any(
        keyword in title_lower
        for keyword in EXCLUDED_TITLE_KEYWORDS
    ):
        return False

    return any(
        keyword in title_lower
        for keyword in TARGET_KEYWORDS
    )

def is_relevant_location(location: str) -> bool:
    if not location:
        return True

    return (
        is_washington_state_location(location)
        or is_us_remote_location(location)
    )

def get_job_details(board_token: str, job_id: int) -> dict:
    url = f"{BASE_URL}/{board_token}/jobs/{job_id}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return response.json()


def collect_greenhouse_jobs(
        board_token: str,
        company_name: str = ""
    ) -> list[dict]:
    url = f"{BASE_URL}/{board_token}/jobs"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    jobs = []

    for job in data.get("jobs", []):
        title = job.get("title", "")

        if not is_relevant_title(title):
            continue

        location = job.get("location", {}).get(
            "name",
            ""
        )

        if not is_relevant_location(location):
            continue

        job_id = job.get("id")
        details = get_job_details(board_token, job_id)
        description = clean_job_description(details.get("content", ""))
        salary_min, salary_max = extract_salary(description)
        years_experience = extract_years_experience(description)
        work_arrangement = extract_work_arrangement(description)
        sponsorship = extract_sponsorship(description)
        required_skills, preferred_skills = (
            extract_required_and_preferred_skills(description)
        )

        jobs.append({
            "id": f"greenhouse-{board_token}-{job_id}",
            "board_token": board_token,
            "external_job_id": job_id,
            "title": details.get("title", "").strip(),
            "company": company_name,
            "description": description,
            "location": details.get("location", {}).get("name", ""),
            "remote": (
                work_arrangement == "remote"
                or location_indicates_remote(location)
            ),
            "work_arrangement": work_arrangement,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "sponsorship": sponsorship,
            "company_size": None,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "minimum_years_experience": years_experience,
            "apply_url": details.get("absolute_url"),
            "source": "greenhouse"
        })

    return jobs