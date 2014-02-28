import datetime as pdatetime

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def datetime(value):
    try:
        return pdatetime.datetime.utcfromtimestamp(value)
    except Exception:
        return "INVALID DATE"
