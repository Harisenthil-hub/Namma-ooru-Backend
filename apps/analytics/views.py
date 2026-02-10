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
from datetime import timedelta



# Create your views here.
class AdminSummaryAnalyticsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self,request):
        cache_key = "admin_summary_analytics"
        cached_data = cache.get(cache_key)

        # If Already cached data availabel
        if cached_data:
            return Response(cached_data,status=status.HTTP_200_OK)

        last_30_days = timezone.now() - timedelta(days=30)
        

        # DB lookups for Analytics
        
        orders = Order.objects.filter(buy_now_clicked_at__gte=last_30_days)

        # Return Total orders
        total_orders = orders.count()
        # Return Pending orders
        pending_orders = orders.filter(order_status='pending').count()
        # Return Confirmed orders
        confirmed_orders = orders.filter(order_status='confirmed').count()
        # Return Confirmed orders Value
        confirmed_value = orders.filter(order_status='confirmed').aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        # Return Pending orders Value
        pending_value = orders.filter(order_status='pending').aggregate(
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

# not connected with front end
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
        today = timezone.localdate()
        days = 30
        date_list = [today - timedelta(days=i) for i in range(days)]
        date_list.reverse()

        current_tz = timezone.get_current_timezone()

        # Total Orders per day
        total_orders_qs = (
            Order.objects
            .annotate(date=TruncDate('created_at', tzinfo=current_tz))
            .values('date')
            .annotate(count=Count('id'))
        )

        # Confirmed Orders per day
        confirmed_qs = (
            Order.objects
            .filter(order_status='confirmed')
            .annotate(date=TruncDate('created_at', tzinfo=current_tz))
            .values('date')
            .annotate(count=Count('id'))
        )

        total_map = {item['date']: item['count'] for item in total_orders_qs if item['date']}
        confirmed_map = {item['date']: item['count'] for item in confirmed_qs if item['date']}
        order_activity_trend = {
            "labels": [str(d) for d in date_list],
            "total_orders": [total_map.get(d, 0) for d in date_list],
            "confirmed_orders": [confirmed_map.get(d, 0) for d in date_list],
        }

        # 2) Order Status Distribution

        last_30_days = timezone.now() - timedelta(days=30)
        status_distribution = ( Order.objects
        .filter(created_at__gte=last_30_days)
        .aggregate(
            pending=Count('id',filter=Q(order_status='pending')),
            confirmed=Count('id',filter=Q(order_status='confirmed')),
            cancelled=Count('id',filter=Q(order_status='cancelled'))
        )
        )

        # 3) Top Products by orders
        top_products = (
            OrderItem.objects
            .filter(order__order_status='confirmed',
                    order__created_at__gte=last_30_days)
            .values('product_name')
            .annotate(orders=Count('id'))
            .order_by('-orders')[:10]
        )

        top_products_by_confirmed_orders = [
            {
                'product': item['product_name'],
                'orders': item['orders']
            }
            for item in top_products
        ]

        # 4) Top Selling Categories (Confirmed)
        top_categories_qs = (
            OrderItem.objects
            .filter(
                order__order_status='confirmed',
                order__created_at__gte=last_30_days
            )
            .values('product__category__name')
            .annotate(
                revenue=Sum('total_price'),
                orders=Count('order', distinct=True)
            )
            .order_by('-revenue')[:7]
        )
        top_categories = []
        total_revenue = Decimal('0.00')
        total_orders = 0

        for item in top_categories_qs:
            revenue = item['revenue'] or Decimal('0.00')
            orders = item['orders']
            total_revenue += revenue
            total_orders += orders
            top_categories.append({
                'category': item['product__category__name'],
                'revenue': float(revenue),
                'orders': orders
            })

        top_selling_categories = {
            "top_categories": top_categories,
            "total_revenue": float(total_revenue),
            "total_orders": total_orders
        }


        data = {
            'order_activity_trend': order_activity_trend,
            'status_distribution': status_distribution,
            'top_products_by_confirmed_orders': top_products_by_confirmed_orders,
            'top_selling_categories': top_selling_categories
        }

        cache.set(cache_key,data,timeout=1)

        return Response(data,status=status.HTTP_200_OK)


class AdminRecentOrdersAnalyticsAPIView(APIView):
    permission_classes=[IsAdminUser]
    
    def get(self,request):
        
        today_date = timezone.localdate()
        cache_key = f"admin_recent_orders{today_date}"
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        # Start and End time of the day
        start_of_day=timezone.make_aware(timezone.datetime.combine(today_date,timezone.datetime.min.time()))
        end_of_day=timezone.make_aware(timezone.datetime.combine(today_date,timezone.datetime.max.time()))
        
        recent_orders_qs = (
            Order.objects
            .filter(created_at__range=(start_of_day,end_of_day))
            .select_related('customer')
            .annotate(items_count=Count('items'))
            .order_by('-created_at')[:2]
        )
        
        
        results=[]
        for order in recent_orders_qs:
            results.append({
                'order_number': order.order_number,
                'customer_name': order.customer.name,
                'phone_no': order.customer.phone_no,
                'total_amount': order.total_amount,
                'items_count': order.items_count,
                'status': order.order_status,
                'created_at': order.created_at
            })
            
        
        data = {
            'date': str(today_date),
            'recent_orders': results
        }
        cache.set(cache_key,data,timeout=1)
    
        return Response(data,status=status.HTTP_200_OK)
        
        
        