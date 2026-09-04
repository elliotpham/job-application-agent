import re


def split_locations(location: str) -> list[str]:
    return [
        part.strip().lower()
        for part in (location or "").split(";")
        if part.strip()
    ]


def is_washington_state_location(location: str) -> bool:
    for part in split_locations(location):

        # Explicitly reject Washington, DC.
        if (
            "district of columbia" in part
            or "washington, dc" in part
        ):
            continue

        # Examples:
        # Seattle, Washington, United States
        # Bellevue, Washington, United States
        # Washington, United States
        if (
            "washington, united states" in part
            or ", washington," in part
        ):
            return True

        # Handle WA abbreviation.
        if re.search(r"(?:^|,\s*)wa(?:,|$)", part):
            return True

    return False


def is_us_remote_location(location: str) -> bool:
    parts = split_locations(location)

    for part in parts:

        # Generic remote. Keep it because there is no
        # explicit foreign-country restriction.
        if part in {
            "remote",
            "fully remote",
        }:
            return True

        us_remote_markers = [
            "united states, remote",
            "remote, united states",
            "usa, remote",
            "remote, usa",
            "us remote",
            "remote - us",
            "remote, us",
        ]

        if any(marker in part for marker in us_remote_markers):
            return True

    return False


def location_indicates_remote(location: str) -> bool:
    return any(
        "remote" in part
        for part in split_locations(location)
    )