from caldav.objects import Todo
import json


def get_attr(todo: Todo, attr: str):
    # Undo line folding https://www.rfc-editor.org/rfc/rfc5545#section-3.1
    if attr in todo.icalendar_instance.walk("vtodo")[0]:
        return todo.icalendar_instance.walk("vtodo")[0][attr]
    else:
        return None


def pretty_print(dict: dict):
    print(json.dumps(dict, sort_keys=True, indent=4))


def uncomplete(todo):
    """Marks the task as uncompleted.

    This method probably will do the wrong thing if the task is a
    recurring task, in version 1.0 this will likely be changed -
    see https://github.com/python-caldav/caldav/issues/127 for
    details.

    """
    if not hasattr(todo.vobject_instance.vtodo, 'status'):
        todo.vobject_instance.vtodo.add('status')
    todo.vobject_instance.vtodo.status.value = 'NEEDS-ACTION'
    if hasattr(todo.vobject_instance.vtodo, 'completed'):
        del todo.vobject_instance.vtodo.completed
    todo.save()
