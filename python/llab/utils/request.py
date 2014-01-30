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
