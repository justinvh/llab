import datetime as pdatetime
import time

from django import template

register = template.Library()


@register.filter
def datetime(value):
    try:
        return pdatetime.datetime.utcfromtimestamp(value)
    except Exception:
        return "INVALID DATE"


@register.filter
def onlytime(value):
    try:
        return time.strftime('%H:%M:%S', time.localtime(value))
    except Exception:
        return "INVALID DATE"
