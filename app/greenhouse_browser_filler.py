from pathlib import Path

from playwright.sync_api import sync_playwright

from app.application_executor import get_ready_to_apply_jobs
from app.application_submission_plan import build_submission_plan


SCREENSHOT_PATH = "data/greenhouse_form_preview.png"


def find_field(page, field_name: str, label: str):
    # Prefer the Greenhouse field name when it exists in the DOM.
    locator = page.locator(
        f'[name="{field_name}"]'
    )

    if locator.count() > 0:
        return locator.first

    # Some forms use the API field name as the element id.
    locator = page.locator(
        f'#{field_name}'
    )

    if locator.count() > 0:
        return locator.first

    # Fallback to the visible question label.
    try:
        locator = page.get_by_label(
            label,
            exact=False
        )

        if locator.count() > 0:
            return locator.first
    except Exception:
        pass

    return None


def fill_location_city(
    page,
    city: str,
    state: str | None = None
):
    print(
        f"Filling Location (City): "
        f"{city}, {state or ''}"
    )

    location = page.get_by_label(
        "Location (City)",
        exact=False
    )

    if location.count() == 0:
        raise RuntimeError(
            "Could not locate Location (City) field"
        )

    location = location.first

    # Clear anything currently in the autocomplete.
    location.fill("")

    # Type instead of fill so the autocomplete's
    # JavaScript receives keyboard/input events.
    location.type(
        city,
        delay=100
    )

    # Give Greenhouse time to load suggestions.
    page.wait_for_timeout(1500)

    # Preferred approach:
    # locate an autocomplete option containing both
    # the city and state.
    suggestions = page.locator(
        '[role="option"]'
    )

    for i in range(suggestions.count()):
        suggestion = suggestions.nth(i)

        try:
            text = suggestion.inner_text().strip()

            city_matches = (
                city.lower()
                in text.lower()
            )

            state_matches = (
                not state
                or state.lower()
                in text.lower()
            )

            if (
                city_matches
                and state_matches
            ):
                print(
                    f"Selecting location: {text}"
                )

                suggestion.click()
                return

        except Exception:
            continue

    # Greenhouse variants do not always expose
    # autocomplete items with role="option".
    # Try visible text instead.
    if state:
        desired_text = (
            f"{city}, {state}"
        )

        matching_text = page.get_by_text(
            desired_text,
            exact=False
        )

        if matching_text.count() > 0:
            print(
                f"Selecting location: "
                f"{desired_text}"
            )

            matching_text.first.click()
            return

    # Final fallback:
    # autocomplete widgets normally support
    # keyboard selection.
    print(
        "Location suggestion not found by DOM. "
        "Trying ArrowDown + Enter."
    )

    location.press("ArrowDown")
    page.wait_for_timeout(300)
    location.press("Enter")

    page.wait_for_timeout(500)


def fill_text(page, action: dict):
    field = find_field(
        page,
        action["field_name"],
        action["label"]
    )

    if field is None:
        raise RuntimeError(
            f"Could not locate text field: "
            f"{action['label']}"
        )

    field.fill(
        str(action["value"])
    )


def upload_file(page, action: dict):
    field = find_field(
        page,
        action["field_name"],
        action["label"]
    )

    # Greenhouse may hide the file input from its visible label.
    if field is None or field.get_attribute("type") != "file":
        file_inputs = page.locator(
            'input[type="file"]'
        )

        if file_inputs.count() == 0:
            raise RuntimeError(
                f"Could not locate file field: "
                f"{action['label']}"
            )

        # Resume is normally the first file field.
        if "resume" in action["label"].lower():
            field = file_inputs.first
        else:
            field = file_inputs.last

    file_path = Path(
        action["file_path"]
    ).resolve()

    if not file_path.exists():
        raise RuntimeError(
            f"File not found: {file_path}"
        )

    field.set_input_files(
        str(file_path)
    )


def select_value(page, action: dict):
    field = find_field(
        page,
        action["field_name"],
        action["label"]
    )

    value_label = action.get(
        "value_label"
    )

    value = action.get(
        "value"
    )

    # Native <select>
    if field is not None:
        tag_name = field.evaluate(
            "(el) => el.tagName.toLowerCase()"
        )

        if tag_name == "select":
            try:
                field.select_option(
                    value=str(value)
                )
            except Exception:
                field.select_option(
                    label=value_label
                )

            return

    # Greenhouse frequently uses custom dropdowns.
    # Find the question by its visible label.
    try:
        control = page.get_by_label(
            action["label"],
            exact=False
        )

        if control.count() > 0:
            control.first.click()

            page.get_by_role(
                "option",
                name=value_label,
                exact=True
            ).click()

            return
    except Exception:
        pass

    # Final fallback: use nearby text/combobox.
    label_text = page.get_by_text(
        action["label"],
        exact=False
    ).first

    container = label_text.locator(
        "xpath=.."
    )

    combobox = container.get_by_role(
        "combobox"
    )

    if combobox.count() > 0:
        combobox.first.click()

        page.get_by_role(
            "option",
            name=value_label,
            exact=True
        ).click()

        return

    raise RuntimeError(
        f"Could not locate select field: "
        f"{action['label']}"
    )


def fill_application(job: dict):
    plan = build_submission_plan(job)

    if not plan["ready"]:
        print("Application is not ready.")

        for item in plan["unresolved"]:
            print(
                "-",
                item["label"],
                item["status"]
            )

        return

    print("\n===== BROWSER FILL TEST =====")
    print(job["title"])
    print(job["company"])
    print(job["apply_url"])
    print()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 1200
            }
        )

        page.goto(
            job["apply_url"],
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(3000)

        for action in plan["actions"]:
            print(
                f"{action['action']}: "
                f"{action['label']}"
            )

            if action["action"] == "fill":
                fill_text(
                    page,
                    action
                )

            elif action["action"] == "upload_file":
                upload_file(
                    page,
                    action
                )

            elif action["action"] == "select":
                select_value(
                    page,
                    action
                )

            elif action["action"] == "select_phone_country":
                select_phone_country(
                    page,
                    action["value"]
                )

            elif action["action"] == "fill_location_city":
                fill_location_city(
                    page,
                    action["city"],
                    action.get("state")
                )

        # IMPORTANT:
        # Do not click Submit yet.
        page.screenshot(
            path=SCREENSHOT_PATH,
            full_page=True
        )

        print()
        print(
            "Form filled successfully."
        )
        print(
            f"Screenshot saved to: "
            f"{SCREENSHOT_PATH}"
        )
        print(
            "The application was NOT submitted."
        )

        browser.close()

def select_phone_country(
    page,
    country: str
):
    print(
        f"Selecting phone country: {country}"
    )

    # Greenhouse's newer application form exposes
    # Country as its own required control before Phone.
    try:
        country_control = page.get_by_label(
            "Country",
            exact=True
        )

        if country_control.count() > 0:
            country_control = country_control.first

            country_control.click()

            option = page.get_by_role(
                "option",
                name=country,
                exact=False
            )

            if option.count() > 0:
                option.first.click()
                return

    except Exception:
        pass

    # Some Greenhouse forms use a React-style custom
    # dropdown whose input is associated with the
    # visible Country text rather than a normal label.
    try:
        country_text = page.get_by_text(
            "Country",
            exact=True
        ).first

        container = country_text.locator(
            "xpath=following::*[@role='combobox'][1]"
        )

        if container.count() > 0:
            container.first.click()

            option = page.get_by_role(
                "option",
                name=country,
                exact=False
            )

            if option.count() > 0:
                option.first.click()
                return

    except Exception:
        pass

    # Final fallback: inspect all comboboxes and choose
    # the first one appearing before the Phone field.
    comboboxes = page.get_by_role(
        "combobox"
    )

    if comboboxes.count() > 0:
        for i in range(comboboxes.count()):
            combo = comboboxes.nth(i)

            try:
                aria_label = (
                    combo.get_attribute("aria-label")
                    or ""
                ).lower()

                name = (
                    combo.get_attribute("name")
                    or ""
                ).lower()

                element_id = (
                    combo.get_attribute("id")
                    or ""
                ).lower()

                if (
                    "country" in aria_label
                    or "country" in name
                    or "country" in element_id
                ):
                    combo.click()

                    option = page.get_by_role(
                        "option",
                        name=country,
                        exact=False
                    )

                    if option.count() > 0:
                        option.first.click()
                        return

            except Exception:
                continue

    raise RuntimeError(
        "Could not locate Country selector"
    )


if __name__ == "__main__":
    jobs = get_ready_to_apply_jobs()

    if not jobs:
        print(
            "No jobs ready to apply."
        )
        raise SystemExit

    fill_application(
        jobs[0]
    )