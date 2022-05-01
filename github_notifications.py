from github import Github
from github.Requester import Requester
from github.Notification import Notification
from configuration import get_config
from interfaces import ToDoSynchronizer
from caldav.objects import Calendar, Todo
from utils import get_attr, uncomplete
from typing import Optional, Dict
from datetime import datetime, timedelta
import pytz
import asyncio

import re


GITHUB_ID_PREFIX = "GitHub Id: "
# For custom requests
DEFAULT_BASE_URL = "https://api.github.com"
DEFAULT_TIMEOUT = 15
DEFAULT_PER_PAGE = 30


class GitHubNotifications(ToDoSynchronizer):
    def __init__(self):
        self._g = Github(get_config("github.notifications.token", str))
        self.__requester = Requester(
            get_config("github.notifications.token", str),
            None,
            None,
            DEFAULT_BASE_URL,
            DEFAULT_TIMEOUT,
            "PyGithub/Python",
            DEFAULT_PER_PAGE,
            True,
            None,
            None,
        )  # type: ignore

    async def sync_todos(self, calendar: Calendar):
        todos = calendar.todos(include_completed=True)
        todo_by_github_id: Dict[int, Todo] = {}

        print(f"{len(todos)} todos found")

        for todo in todos:
            github_id = self._get_github_id(todo)
            if github_id:
                todo_by_github_id[github_id] = todo

        since = datetime.now() - timedelta(days=get_config("github.notifications.last", int))
        notifications = list(self._g.get_user().get_notifications(all=True, since=since))

        print(f"{len(notifications)} notifications found")

        for n in notifications:
            n_id = int(n.id)
            if n_id in todo_by_github_id:
                # We know this item already
                self._sync_todo_with_notification(n, todo_by_github_id[n_id])
                del todo_by_github_id[n_id]
            else:
                # this must be a new item
                self._create_todo_from_notification(n, calendar)

            # Setting the delay to 0 provides an
            # optimized path to allow other tasks to run.
            # https://docs.python.org/3/library/asyncio-task.html#id5
            await asyncio.sleep(0)

        for key, todo in todo_by_github_id.items():
            # Todos that were "done" in Github
            print(f"deleting dangling todo {key}")
            todo.delete()

    def _get_github_id(self, todo: Todo) -> Optional[int]:
        desc = get_attr(todo, "DESCRIPTION")
        if not desc:
            return None
        match = re.search(GITHUB_ID_PREFIX + r"(\d+)", desc)
        if match:
            return int(match.group(1))
        else:
            return None

    def _sync_todo_with_notification(self, n: Notification, todo: Todo):
        print(f"update {n.id} {n.subject.title}")

        todo_last_modified_attr = get_attr(todo, "LAST-MODIFIED")
        todo_last_modified = None
        if todo_last_modified_attr:
            todo_last_modified = todo_last_modified_attr.dt
        notification_last_modified = datetime.strptime(
            n.raw_data["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
        )
        notification_last_modified = pytz.UTC.localize(notification_last_modified)

        if todo_last_modified is None and notification_last_modified is None:
            return  # same state
        if todo_last_modified is None:
            self._sync_to_caldav(n, todo)
            return
        if notification_last_modified is None:
            # may never happen
            self._sync_to_github(n, todo)
            return
        else:
            if todo_last_modified < notification_last_modified:
                self._sync_to_caldav(n, todo)
            else:
                self._sync_to_github(n, todo)

    def _sync_to_github(self, n: Notification, todo: Todo):
        print("caldav -> github")
        if get_attr(todo, "COMPLETED") and n.unread:
            print("mark as read")
            n.mark_as_read()
            return
        # Mark as unread currently not supported by api

        print("do nothing")
        return

    def _sync_to_caldav(self, n: Notification, todo: Todo):
        print("github -> caldav")
        if n.unread and get_attr(todo, "COMPLETED"):
            print("mark as uncompleted")
            uncomplete(todo)
            return
        if not n.unread and not get_attr(todo, "COMPLETED"):
            print("mark as completed")
            todo.complete()
            return

        print("do nothing")
        return

    def _create_todo_from_notification(self, n: Notification, calendar: Calendar):
        print(f"create {n.id} {n.subject.title}")

        kwargs = {
            "summary": f"[GH] {n.subject.title}",
            "status": "NEEDS-ACTION",
        }

        desc = f"""{n.repository.full_name}

{n.repository.description}

You are getting this because you are {n.reason}.

{GITHUB_ID_PREFIX}{n.id}"""

        if n.subject.url is not None:
            # user private attribute because custom requests are not supported
            _, data = self.__requester.requestJsonAndCheck(
                "GET", n.subject.url.removeprefix(DEFAULT_BASE_URL)
            )
            if data is not None:
                if "html_url" in data:
                    kwargs["location"] = data["html_url"].strip()

        kwargs["description"] = desc

        todo = calendar.save_todo(**kwargs)

        if not n.unread:
            todo.complete()