from datetime import timedelta, datetime
from django.utils import timezone
from apps.orders.models import Order


def get_date_range(request):
    range_param = request.GET.get('range','1month') # default = 1month
    now = timezone.now()
    
    if range_param == 'today':
        start_date = now.replace(hour=0,minute=0,second=0,microsecond=0)
    elif (range_param == '1week'):
        start_date = now - timedelta(days=7)
    elif (range_param == '1month'):
        start_date = now - timedelta(days=30)
    elif (range_param == '3month'):
        start_date = now - timedelta(days=90)
    elif (range_param == '1year'):
        start_date = now - timedelta(days=365)
    elif (range_param == '3year'):
        start_date = now - timedelta(days=365*3)
    elif (range_param == '5year'):
        start_date = now - timedelta(days=365*5)
    elif (range_param == 'max'):
        first_order = Order.objects.earliest('created_at')
        start_date = first_order.created_at
    else:
        start_date = now - timedelta(days=30)
        
    return start_date,now,range_param

def normalize(value):
    if isinstance(value, datetime):
        return timezone.localtime(value).replace(
            minute=0, second=0, microsecond=0
        )
    return value