from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Order

@shared_task
def cancel_stale_orders():
    cutoff_time = timezone.now() - timedelta(minutes=1)

    updated = Order.objects.filter(
        order_status='pending',
        created_at__lt=cutoff_time
    ).update(
        order_status='cancelled'
    )

    return f"Cancelled {updated} stale order"