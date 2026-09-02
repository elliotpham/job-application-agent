import json


def load_jobs(filename: str) -> list[dict]:
    """
    Load jobs from a JSON file.

    This is our first job source.
    Later we can replace this with real job APIs/feeds.
    """

    with open(filename, "r") as file:
        return json.load(file)


def collect_jobs(filename: str = "data/jobs.json") -> list[dict]:
    """Collect and return job postings."""

    jobs = load_jobs(filename)

    print(f"Collected {len(jobs)} jobs")

    return jobs


if __name__ == "__main__":
    jobs = collect_jobs()

    for job in jobs:
        print(
            f"{job.get('title')} at {job.get('company')}"
        )