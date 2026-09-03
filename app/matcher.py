import re


def normalize(text: str) -> str:
    """Normalize text for case-insensitive matching."""
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def contains_skill(text: str, skill: str) -> bool:
    """
    Check whether a skill appears in the job text.

    Uses word boundaries to avoid accidental substring matches.
    """
    text = normalize(text)
    skill = normalize(skill)

    # Handle common variations
    aliases = {
        "restful apis": ["rest", "restful", "restful api", "rest api"],
        "kubernetes": ["kubernetes", "k8s"],
        "spring boot": ["spring boot"],
        "microservices architecture": ["microservices", "microservice"],
        "amazon web services": ["aws"],
        "google cloud": ["gcp", "google cloud"],
    }

    variants = aliases.get(skill, [skill])

    for variant in variants:
        pattern = r"\b" + re.escape(variant) + r"\b"
        if re.search(pattern, text):
            return True

    return False

def calculate_skill_score(job: dict, profile: dict):
    candidate_skills = {
        skill.strip().lower()
        for skill in profile.get("skills", [])
    }

    required_skills = job.get("required_skills", [])
    preferred_skills = job.get("preferred_skills", [])

    matched_required = [
        skill
        for skill in required_skills
        if skill.strip().lower() in candidate_skills
    ]

    missing_required = [
        skill
        for skill in required_skills
        if skill.strip().lower() not in candidate_skills
    ]

    matched_preferred = [
        skill
        for skill in preferred_skills
        if skill.strip().lower() in candidate_skills
    ]

    # Required skills determine the core technical fit.
    if required_skills:
        required_score = (
            len(matched_required) / len(required_skills)
        ) * 100

        # Preferred skills are a bonus, not a penalty.
        if preferred_skills:
            preferred_ratio = (
                len(matched_preferred) / len(preferred_skills)
            )

            technical_score = required_score + (
                (100 - required_score)
                * 0.10
                * preferred_ratio
            )
        else:
            technical_score = required_score

    # Some postings, like this Datadog one, don't name any
    # specific required technologies. In that case, use the
    # preferred/bonus technologies to estimate technical fit.
    elif preferred_skills:
        technical_score = (
            len(matched_preferred) / len(preferred_skills)
        ) * 100

    # No technical information in the posting = neutral score.
    else:
        technical_score = 70

    matched_skills = matched_required + matched_preferred

    return (
        round(technical_score),
        matched_skills,
        missing_required,
    )

def calculate_role_score(job: dict, profile: dict) -> int:
    """Score how well the job title matches the candidate's target roles."""

    title = normalize(job.get("title", ""))

    target_roles = profile.get("target_roles", [])

    for role in target_roles:
        if normalize(role) in title:
            return 100

    # Strong backend/Java signals
    backend_keywords = [
        "backend",
        "back-end",
        "java",
        "software engineer",
        "software developer",
    ]

    matches = sum(
        1 for keyword in backend_keywords
        if keyword in title
    )

    if matches >= 2:
        return 90

    if matches == 1:
        return 70

    return 20


def calculate_seniority_score(job: dict, profile: dict) -> int:
    """Score whether the job seniority fits the candidate."""

    title = normalize(job.get("title", ""))

    senior_keywords = [
        "senior",
        "sr.",
        "sr ",
        "staff",
        "principal",
    ]

    mid_keywords = [
        "mid",
        "mid-level",
        "ii",
        "2",
        "software engineer",
    ]

    junior_keywords = [
        "junior",
        "jr.",
        "jr ",
        "entry",
        "intern",
    ]

    if any(keyword in title for keyword in junior_keywords):
        return 0

    if any(keyword in title for keyword in senior_keywords):
        return 100

    if any(keyword in title for keyword in mid_keywords):
        return 90

    return 60


def calculate_location_score(job: dict, profile: dict) -> tuple[int, bool]:
    """
    Return location score and whether the job passes the hard location filter.
    """

    location = normalize(job.get("location", ""))
    remote = job.get("remote", False)

    if remote:
        return 100, True

    if "remote" in location:
        return 100, True

    # Washington locations
    washington_locations = [
        "washington",
        "seattle",
        "bellevue",
        "redmond",
        "kirkland",
        "renton",
        "tacoma",
        "bothell",
        "everett",
    ]

    if any(city in location for city in washington_locations):
        return 100, True

    # User does not want to relocate
    if profile.get("willing_to_relocate") is False:
        return 0, False

    return 50, True


def calculate_salary_score(job: dict, profile: dict) -> tuple[int, bool]:
    """
    Score salary and determine whether the job passes the hard salary filter.
    """

    candidate_min = profile["salary"]["minimum_base"]

    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")

    # Salary not disclosed.
    # Don't reject the job because of missing information.
    if salary_min is None and salary_max is None:
        return 70, True

    # If maximum salary is below candidate minimum,
    # the job is a hard reject.
    if salary_max is not None and salary_max < candidate_min:
        return 0, False

    # If salary range overlaps candidate range.
    return 100, True


def calculate_sponsorship_score(job: dict, profile: dict) -> tuple[int, bool]:
    """
    Handle sponsorship requirements.

    Explicitly refusing sponsorship is a hard rejection.
    Unknown sponsorship policy is not rejected.
    """

    requires_sponsorship = profile["work_authorization"][
        "requires_sponsorship_now_or_future"
    ]

    if not requires_sponsorship:
        return 100, True

    sponsorship = normalize(job.get("sponsorship", ""))

    if any(
        phrase in sponsorship
        for phrase in [
            "no sponsorship",
            "will not sponsor",
            "does not sponsor",
            "unable to sponsor",
            "without sponsorship",
        ]
    ):
        return 0, False

    if any(
        phrase in sponsorship
        for phrase in [
            "sponsorship available",
            "will sponsor",
            "visa sponsorship",
        ]
    ):
        return 100, True

    # Unknown
    return 60, True


def calculate_company_score(job: dict, profile: dict) -> int:
    """Score company size based on candidate preference."""

    company_size = normalize(job.get("company_size", ""))

    preferences = profile.get("company_preferences", {})

    if "large" in company_size:
        return round(preferences.get("large", 1.0) * 100)

    if "mid" in company_size:
        return round(preferences.get("mid_size", 0.8) * 100)

    if "startup" in company_size:
        return round(preferences.get("startup", 0.6) * 100)

    return 70


def calculate_match(job: dict, profile: dict) -> dict:
    """
    Calculate overall job match score.

    Hard filters override the numerical score.
    """

    skill_score, matched_skills, missing_skills = calculate_skill_score(
        job, profile
    )

    role_score = calculate_role_score(job, profile)
    seniority_score = calculate_seniority_score(job, profile)

    location_score, location_pass = calculate_location_score(
        job, profile
    )

    salary_score, salary_pass = calculate_salary_score(
        job, profile
    )

    sponsorship_score, sponsorship_pass = calculate_sponsorship_score(
        job, profile
    )

    company_score = calculate_company_score(job, profile)

    # Weighted score
    score = round(
        skill_score * 0.35
        + role_score * 0.20
        + seniority_score * 0.10
        + location_score * 0.10
        + salary_score * 0.10
        + sponsorship_score * 0.05
        + company_score * 0.05
    )

    hard_filter_failures = []

    if not location_pass:
        hard_filter_failures.append("Location does not match preferences")

    if not salary_pass:
        hard_filter_failures.append(
            "Salary is below minimum requirement"
        )

    if not sponsorship_pass:
        hard_filter_failures.append(
            "Employer does not provide required sponsorship"
        )

    minimum_score = profile["application_strategy"]["minimum_match_score"]

    if hard_filter_failures:
        recommendation = "SKIP"
    elif score >= minimum_score:
        recommendation = "APPLY"
    else:
        recommendation = "SKIP"

    return {
        "match_score": score,
        "recommendation": recommendation,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "hard_filter_failures": hard_filter_failures,
        "breakdown": {
            "technical_skills": skill_score,
            "role_fit": role_score,
            "seniority": seniority_score,
            "location": location_score,
            "salary": salary_score,
            "sponsorship": sponsorship_score,
            "company": company_score,
        },
    }


if __name__ == "__main__":
    import json

    with open("candidate/profile.json") as file:
        profile = json.load(file)

    job = {
        "title": "Senior Backend Java Engineer",
        "description": """
        We are looking for a Senior Backend Engineer with strong
        Java, Spring Boot, Kafka, AWS, Docker and Kubernetes experience.
        Experience with REST APIs and microservices is required.
        """,
        "location": "Seattle, WA",
        "remote": False,
        "salary_min": 140000,
        "salary_max": 175000,
        "sponsorship": "Sponsorship available",
        "company_size": "large",
        "required_skills": [
            "Java",
            "Spring Boot",
            "Kafka",
            "AWS",
            "Docker",
            "Kubernetes",
            "RESTful APIs",
            "Microservices Architecture",
        ],
        "preferred_skills": [
            "GraphQL",
            "Redis",
            "Jenkins",
        ],
    }

    result = calculate_match(job, profile)

    print(json.dumps(result, indent=2))