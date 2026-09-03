def normalize_job(raw_job: dict) -> dict:
    return {
        "id": raw_job.get("id"),
        "title": raw_job.get("title", "").strip(),
        "company": raw_job.get("company", ""),
        "description": raw_job.get("description", ""),
        "location": raw_job.get("location", ""),
        "remote": raw_job.get("remote", False),
        "work_arrangement": raw_job.get("work_arrangement"),
        "salary_min": raw_job.get("salary_min"),
        "salary_max": raw_job.get("salary_max"),
        "sponsorship": raw_job.get("sponsorship"),
        "company_size": raw_job.get("company_size"),
        "required_skills": raw_job.get("required_skills", []),
        "preferred_skills": raw_job.get("preferred_skills", []),
        "minimum_years_experience": raw_job.get(
            "minimum_years_experience"
        ),
        "apply_url": raw_job.get("apply_url"),
        "source": raw_job.get("source")
    }


def normalize_jobs(raw_jobs: list[dict]) -> list[dict]:
    return [normalize_job(job) for job in raw_jobs]