import time
import datetime
import pytz
from django.utils.timezone import now


def timing(get_response):
    def middleware(request):
        tz_nsk = pytz.timezone('Asia/Novosibirsk')
        request.current_time = now().now(tz=tz_nsk).strftime("%H:%M:%S")
        t1 = time.time()
        response = get_response(request)
        t2 = time.time()
        return response
    return middleware
