import user_streams
from django.template.loader import render_to_string


def post_or_none(request):
    """post_or_none -> dict.

    Returns the POST object if available, otherwise None.

    """
    return request.POST if request.method == 'POST' else None


def get_or_none(request):
    """get_or_none -> dict.

    Returns the GET object if available, otherwise None.

    """
    return request.GET if request.method == 'GET' else None


def notify_users(users, template, context):
    users = users if isinstance(users, (list, tuple)) else [users]
    content = render_to_string(template, context)
    user_streams.add_stream_item(users, content)
