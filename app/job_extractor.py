import html
import re

from bs4 import BeautifulSoup


def clean_job_description(raw_html: str) -> str:
    if not raw_html:
        return ""

    # Greenhouse content is HTML-escaped, so decode entities first.
    decoded = html.unescape(raw_html)

    soup = BeautifulSoup(decoded, "html.parser")

    # Preserve useful separation between paragraphs/list items.
    text = soup.get_text(separator="\n")

    # Clean excessive whitespace.
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)

    return "\n".join(lines)


def extract_salary(text: str) -> tuple[int | None, int | None]:
    salary_pattern = re.search(
        r"\$([\d,]+)\s*[—–-]\s*\$([\d,]+)",
        text
    )

    if not salary_pattern:
        return None, None

    salary_min = int(salary_pattern.group(1).replace(",", ""))
    salary_max = int(salary_pattern.group(2).replace(",", ""))

    return salary_min, salary_max


def extract_years_experience(text: str) -> int | None:
    match = re.search(
        r"(\d+)\+?\s+years?\s+of\s+experience",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    return int(match.group(1))


def extract_work_arrangement(text: str) -> str | None:
    text_lower = text.lower()

    if "#li-hybrid" in text_lower:
        return "hybrid"

    if "#li-remote" in text_lower:
        return "remote"

    if "#li-onsite" in text_lower or "#li-on-site" in text_lower:
        return "onsite"

    return None

SKILL_ALIASES = {
    "Java": ["java"],
    "Spring Boot": ["spring boot"],
    "Kafka": ["kafka"],
    "Redis": ["redis"],
    "Cassandra": ["cassandra"],
    "Python": ["python"],
    "Go": ["go", "golang"],
    "C": [" c "],
    "C++": ["c++"],
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "GraphQL": ["graphql"],
    "RESTful APIs": ["rest api", "restful api", "restful"],
    "Microservices Architecture": ["microservices", "microservice"],
    "Elasticsearch": ["elasticsearch"],
    "Jenkins": ["jenkins"],
    "RabbitMQ": ["rabbitmq"],
    "MongoDB": ["mongodb"],
}


def find_skills(text: str) -> list[str]:
    text_lower = f" {text.lower()} "

    found = []

    for skill, aliases in SKILL_ALIASES.items():
        if any(alias in text_lower for alias in aliases):
            found.append(skill)

    return found


def extract_required_and_preferred_skills(text: str) -> tuple[list[str], list[str]]:
    text_lower = text.lower()

    bonus_index = text_lower.find("bonus points:")

    if bonus_index == -1:
        return find_skills(text), []

    required_section = text[:bonus_index]
    preferred_section = text[bonus_index:]

    required_skills = find_skills(required_section)
    preferred_skills = find_skills(preferred_section)

    # Don't count something as preferred if it was already required.
    preferred_skills = [
        skill
        for skill in preferred_skills
        if skill not in required_skills
    ]

    return required_skills, preferred_skills