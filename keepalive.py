"""Open each configured demo app and wake it when necessary."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


ROOT = Path(__file__).resolve().parent
PROJECTS_FILE = ROOT / "projects.json"
NAVIGATION_TIMEOUT_MS = 60_000
WAKE_TIMEOUT_SECONDS = 90
MAX_RETRIES = 2


def _body_text(page: Page) -> str:
    try:
        return page.locator("body").inner_text(timeout=5_000).lower()
    except PlaywrightTimeoutError:
        return ""


def _is_sleeping(page: Page, project_type: str) -> bool:
    text = _body_text(page)
    if project_type == "streamlit":
        return (
            "this app has gone to sleep" in text
            or "this app is sleeping" in text
            or "app is sleeping" in text
            or "get this app back up" in text
        )
    return "sleeping" in text or "space is sleeping" in text


def _click_wake_control(page: Page, project_type: str) -> bool:
    patterns = (
        r"yes,?\s*get this app back up!|get this app back up|wake up|restart|relaunch"
        if project_type == "streamlit"
        else r"restart|relaunch|wake up|start"
    )
    buttons = page.get_by_role("button")
    count = buttons.count()

    for index in range(count):
        button = buttons.nth(index)
        try:
            label = button.inner_text(timeout=2_000)
            if re.search(patterns, label, re.IGNORECASE):
                button.click(timeout=10_000)
                return True
        except Exception:
            continue
    return False


def _has_wake_control(page: Page, project_type: str) -> bool:
    patterns = (
        r"yes,?\s*get this app back up!|get this app back up|wake up|restart|relaunch"
        if project_type == "streamlit"
        else r"restart|relaunch|wake up|start"
    )
    for index in range(page.get_by_role("button").count()):
        try:
            if re.search(patterns, page.get_by_role("button").nth(index).inner_text(timeout=2_000), re.IGNORECASE):
                return True
        except Exception:
            continue
    return False


def _wait_until_awake(page: Page, project_type: str) -> None:
    deadline = time.monotonic() + WAKE_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if not _is_sleeping(page, project_type):
            return
        page.wait_for_timeout(2_000)
    raise RuntimeError(f"the {project_type} app still shows a sleeping state after 90 seconds")


def _check_project(page: Page, project: dict[str, str]) -> None:
    project_type = project["type"]
    page.goto(project["url"], wait_until="load", timeout=NAVIGATION_TIMEOUT_MS)

    if project_type == "streamlit":
        if _is_sleeping(page, project_type) and not _click_wake_control(page, project_type):
            raise RuntimeError("sleeping message found, but no wake-up button was available")
        if _is_sleeping(page, project_type):
            _wait_until_awake(page, project_type)
    else:
        if _is_sleeping(page, project_type) or _has_wake_control(page, project_type):
            if not _click_wake_control(page, project_type):
                raise RuntimeError("a sleeping/restart state was found, but no restart button was available")
            _wait_until_awake(page, project_type)


def _load_projects() -> list[dict[str, str]]:
    with PROJECTS_FILE.open(encoding="utf-8") as file:
        data: Any = json.load(file)
    if not isinstance(data, list):
        raise ValueError("projects.json must contain a list of project objects")

    projects: list[dict[str, str]] = []
    for index, project in enumerate(data, start=1):
        if not isinstance(project, dict):
            raise ValueError(f"project {index} must be an object")
        if not all(isinstance(project.get(key), str) for key in ("name", "url", "type")):
            raise ValueError(f"project {index} must contain string name, url, and type fields")
        if project["type"] not in {"streamlit", "huggingface"}:
            raise ValueError(f"project {index} has unsupported type {project['type']!r}")
        projects.append({"name": project["name"], "url": project["url"], "type": project["type"]})
    return projects


def main() -> int:
    try:
        projects = _load_projects()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 1

    failures = 0
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for project in projects:
                started = time.monotonic()
                error_message = ""
                succeeded = False
                for attempt in range(1, MAX_RETRIES + 2):
                    page = browser.new_page()
                    try:
                        _check_project(page, project)
                        succeeded = True
                        break
                    except Exception as error:  # Keep checking the remaining projects.
                        error_message = str(error)
                    finally:
                        page.close()

                elapsed = time.monotonic() - started
                if succeeded:
                    print(f"{project['name']}: OK ({elapsed:.1f}s)")
                else:
                    failures += 1
                    print(f"{project['name']}: FAILED ({elapsed:.1f}s) - {error_message}")
        finally:
            browser.close()

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
