#!/usr/bin/env python3

"""Sync CalDav with popular providers"""

import caldav
import asyncio
from typing import Dict, Callable, Awaitable
from interfaces import ToDoSynchronizer
from caldav.objects import Calendar, Principal
from configuration import get_config
from github_notifications import GitHubNotifications


def _get_calendar(principal: Principal) -> Calendar:
    name = calendar_name = get_config("caldav.calendar", str)

    for cal in principal.calendars():
        if cal.name == name:
            return cal
    raise KeyError(f"Calendar {calendar_name} does not exist.")


async def _run_every(function: Callable[[], Awaitable[None]], timeout_s: int):
    while True:
        await function()
        await asyncio.sleep(timeout_s)


async def main():
    client = caldav.DAVClient(
        url=get_config("caldav.url", str),
        username=get_config("caldav.user", str),
        password=get_config("caldav.password", str),
    )

    todo_synchronizer: Dict[str, ToDoSynchronizer] = {
        "github.notifications": GitHubNotifications()
    }

    with client:
        principal = client.principal()
        calendar = _get_calendar(principal)

        await asyncio.gather(
            *[
                _run_every(lambda: syncr.sync_todos(calendar), get_config(f"{key_prefix}.interval", int))
                for key_prefix, syncr in todo_synchronizer.items()
                if get_config(f"{key_prefix}.enabled", bool)
            ]
        )

        github = GitHubNotifications()
        await github.sync_todos(calendar)


if __name__ == "__main__":
    asyncio.run(main())
