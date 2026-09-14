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
    phone = page.locator(
        '[name="phone"]'
    )

    if phone.count() == 0:
        raise RuntimeError(
            "Could not locate phone input"
        )

    phone = phone.first

    # Find the closest container around the phone field
    # that also contains a dropdown/combobox.
    container = phone.locator(
        "xpath=ancestor::div[.//*[@role='combobox']][1]"
    )

    if container.count() > 0:
        combobox = container.get_by_role(
            "combobox"
        )

        if combobox.count() > 0:
            combobox.first.click()

            page.get_by_role(
                "option",
                name=country,
                exact=False
            ).first.click()

            return

    # Fallback for Greenhouse variants where the
    # country selector is exposed globally by label.
    country_select = page.get_by_role(
        "combobox",
        name="Country",
        exact=False
    )

    if country_select.count() > 0:
        country_select.first.click()

        page.get_by_role(
            "option",
            name=country,
            exact=False
        ).first.click()

        return

    raise RuntimeError(
        "Could not locate phone country selector"
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