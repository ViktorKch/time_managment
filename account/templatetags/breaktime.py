from django import template
import pytz
import datetime

register = template.Library()

@register.filter()
def breaktime(timedeltaobj):
    if datetime.datetime.now(tz=pytz.timezone('Asia/Novosibirsk')) - timedeltaobj >= datetime.timedelta(minutes=15):
        return True
    else:
        return False