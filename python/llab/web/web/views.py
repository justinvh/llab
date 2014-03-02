from django import http
from .management.commands.jsurl import Command as JSUrl


def urls(request):
    content = JSUrl.autocreate()
    return http.HttpResponse(content, content_type='text/javascript')
