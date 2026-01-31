from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count, Q
from django.core.cache import cache
from rest_framework import status
from decimal import Decimal
from apps.orders.models import Order, OrderItem
from django.utils import timezone
from django.db.models.functions import TruncDate


# Create your views here.
class AdminSummaryAnalyticsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self,request):
        cache_key = "admin_summary_analytics"
        cached_data = cache.get(cache_key)

        # If Already cached data availabel
        if cached_data:
            return Response(cached_data,status=status.HTTP_200_OK)


        # DB lookups for Analytics

        # Return Total orders
        total_orders = Order.objects.filter(buy_now_clicked_at__isnull=False).count()
        # Return Pending orders
        pending_orders = Order.objects.filter(order_status='pending').count()
        # Return Confirmed orders
        confirmed_orders = Order.objects.filter(order_status='confirmed').count()
        # Return Confirmed orders Value
        confirmed_value = Order.objects.filter(order_status='confirmed').aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        # Return Pending orders Value
        pending_value = Order.objects.filter(order_status='pending').aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')

        conversion_rate = Decimal('0.00')
        if total_orders > 0 :
            conversion_rate = (
                (Decimal(confirmed_orders) / Decimal(total_orders)) * 100 ).quantize(Decimal("0.01"))

        data = {
            'total_orders': total_orders,
            'pending_order': pending_orders,
            'confirmed_orders': confirmed_orders,
            'pending_orders': pending_orders,
            'conversion_rate': conversion_rate,
            'confirmed_value': confirmed_value,
            'pending_value': pending_value
        }

        cache.set(cache_key,data, timeout=60)

        return Response(data, status=status.HTTP_200_OK)


class AdminPendingAnalyticsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self,request):

        cache_key = 'admin_pending_analytics'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data,status=status.HTTP_200_OK)

        now = timezone.now()


        pending_orders = (
            Order.objects
            .filter(order_status='pending')
            .select_related('customer')
            .prefetch_related('items')
            .annotate(items_count=Count('items'))
            .order_by('-buy_now_clicked_at')
        )

        results = []
        for order in pending_orders:
            pending_minutes = int(
                (now - order.buy_now_clicked_at).total_seconds() // 60
            )

            results.append({
                'order_number': order.order_number,
                'customer_name': order.customer.name,
                'phone_no': order.customer.phone_no,
                'total_amount': order.total_amount,
                'items_count': order.items_count,
                'pending_minutes': pending_minutes,
                'buy_now_clicked_at': order.buy_now_clicked_at,
            })

        data = {
            'count': pending_orders.count(),
            'results': results
        }

        cache.set(cache_key, data, timeout=10)

        
        return Response(data,status=status.HTTP_200_OK)


class AdminChartAnalyticsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self,request):
        cache_key = 'admin_charts_analytics'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data,status=status.HTTP_200_OK)


        # 1) Order Activity Trend (Intent vs Confirmed)

        total_orders_qs = (
            Order.objects
            .filter(buy_now_clicked_at__isnull=False)
            .annotate(date=TruncDate('buy_now_clicked_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        confirmed_qs = (
            Order.objects
            .filter(order_status='confirmed')
            .annotate(date=TruncDate('buy_now_clicked_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )


        total_orders_map = {str(i['date']): i['count'] for i in total_orders_qs}
        confirmed_map = {str(c['date']): c['count'] for c in confirmed_qs}


        labels = sorted(set(total_orders_map.keys()) | set(confirmed_map.keys()))

        order_activity_trend = {
            'labels': labels,
            'total_orders': [ total_orders_map.get(d,0) for d in labels ],
            'confirmed_orders': [ confirmed_map.get(d,0) for d in labels ],
        }

        # 2) Order Status Distribution
        status_distribution = Order.objects.aggregate(
            pending=Count('id',filter=Q(order_status='pending')),
            confirmed=Count('id',filter=Q(order_status='confirmed')),
            cancelled=Count('id',filter=Q(order_status='cancelled'))
        )


        # 3) Top Products by orders
        top_products = (
            OrderItem.objects
            .filter(order__order_status='confirmed')
            .values('product_name')
            .annotate(orders=Count('id'))
            .order_by('-orders')[:5]
        )

        top_products_by_confirmed_orders = [
            {
                'product': item['product_name'],
                'orders': item['orders']
            }
            for item in top_products
        ]

        # 4) Top Selling Categories (Confirmed)

        top_categories = (
            OrderItem.objects
            .filter(order__order_status='confirmed')
            .values('product__category')
            .annotate(
                revenue=Sum('total_price'),
                orders=Count('order',distinct=True)
            )
            .order_by('-revenue')[:5]
        )

        top_selling_categories = [
            {
                'category': item['product__category'],
                'revenue': item['revenue'] or Decimal('0.00'),
                'orders': item['orders']
            }
            for item in top_categories
        ]


        data = {
            'order_activity_trend': order_activity_trend,
            'order_status_distribution': status_distribution,
            'top_products_by_confirmed_orders': top_products_by_confirmed_orders,
            'top_selling_categories': top_selling_categories
        }

        cache.set(cache_key,data,timeout=1)

        return Response(data,status=status.HTTP_200_OK)

