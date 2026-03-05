from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Prefetch
from .models import Order, OrderItem



def get_filtered_orders(request):
    
    qs = Order.objects.select_related(
            'customer',
            'shipping_address'
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('product').only(
                    'order_id',
                    'product_id',
                    'quantity',
                    'unit_price',
                    'variant_weight'
                )
            )
        ).only(
            'order_number', 'order_status', 'total_amount', 'created_at',
             'customer__name', 'customer__phone_no','customer__alternate_phone_no','shipping_address__street','shipping_address__city','shipping_address__pincode',
             'shipping_address__landmark'
        ).order_by('-created_at')


    status = request.query_params.get('status')
    search = request.query_params.get('search')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    date = request.query_params.get('date')
    quick = request.query_params.get('quick')
    min_amount = request.query_params.get('min_amount')
    max_amount = request.query_params.get('max_amount')
    
    
    if status:
            qs = qs.filter(order_status=status)

    if search:
        qs = qs.filter(
            Q(order_number__icontains=search) |
            Q(customer__phone_no__icontains=search) |
            Q(customer__name__icontains=search)
        )
        
    # Single date
    if date:
        qs = qs.filter(created_at__date=date)
    
    # Date range
    if start_date and end_date:
        qs = qs.filter(create_at__range=[start_date,end_date])
    
    
    if quick:
        now = timezone.now()
        
        if quick == 'today':
            qs = qs.filter(created_at__date=now.date())
            
        elif quick == 'yesterday':
            qs = qs.filter(created_at__date=(now - timedelta(days=1)).date())
        
        elif quick == 'last7days':
            qs = qs.filter(created_at__gte=now - timedelta(days=7))
            
        elif quick == 'last30days':
            qs = qs.filter(created_at__gte=now - timedelta(days=30))
            
            
    if min_amount:
        qs = qs.filter(total_amount__gte=min_amount)

    
    if min_amount:
        qs = qs.filter(total_amount__lte=min_amount)
        
        
    return qs
    
