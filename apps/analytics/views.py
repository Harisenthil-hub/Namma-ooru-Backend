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
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncHour
from datetime import timedelta
from .utils import get_date_range, normalize
from .pagination import AdminDashboardRecentOrderPagination



# Create your views here.
class AdminSummaryAnalyticsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self,request):
        start_date, end_date, range_param = get_date_range(request)
        cache_key = f"admin_summary_analytics_{range_param}"
        cached_data = cache.get(cache_key)

        # If Already cached data availabel
        if cached_data:
            return Response(cached_data,status=status.HTTP_200_OK)
        

        # DB lookups for Analytics
        if start_date:
            orders = Order.objects.filter(
                buy_now_clicked_at__range=(start_date,end_date)
            )
        else:
            orders = Order.objects.all()

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
        start_date, end_date, range_param = get_date_range(request)
        cache_key = f'admin_charts_analytics_{range_param}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data,status=status.HTTP_200_OK)
        
        
        # Base Query 
        orders_base = Order.objects.all()
        
        if range_param != 'max' and start_date:
            orders_base = orders_base.filter(
                buy_now_clicked_at__range=(start_date,end_date)
            )
            
        current_tz = timezone.get_current_timezone()
        
        date_list = []
        
        # Grouping Logic
        
        if range_param == 'today':
            trunc_func = TruncHour
            
            local_now = timezone.localtime(end_date)
            start_of_day = local_now.replace(
                hour=0,minute=0,second=0,microsecond=0
            )
            
            date_list = []
            current = start_of_day
            
            while current <= local_now:
                date_list.append(current)
                current += timedelta(hours=1)
                
        elif range_param == 'max':
            trunc_func = TruncMonth
            
            first_order = Order.objects.order_by('created_at').first()
            if first_order:
                start = first_order.created_at.date().replace(day=1)
            else:
                start = timezone.localdate().replace(day=1)
                
            end = timezone.localdate().replace(day=1)
            
            
            while current <= end:
                date_list.append(current)
                # Moving 1 month forward
                if current.month == 12:
                    current = current.replace(year=current.year+1,month=1)
                else:
                    current = current.replace(month=current.month+1)
                    
        else:
            total_days = (end_date.date() - start_date.date()).days
            
            if total_days <= 90:
                trunc_func = TruncDate
                step_days = 1
            elif total_days <= 365:
                trunc_func = TruncWeek
                step_days = 7
            else:
                trunc_func = TruncMonth
                step_days = 30
                
            current = start_date.date()
            
            while current <= end_date.date():
                date_list.append(current)
                current += timedelta(days=step_days)
                    
                

        # 1) Order Activity Trend (Intent vs Confirmed) 
        # Total Orders per day
        
        total_orders_qs = (
            orders_base
            .annotate(date=trunc_func('buy_now_clicked_at', tzinfo=current_tz))
            .values('date')
            .annotate(count=Count('id'))
        )

        # Confirmed Orders per day
        confirmed_qs = (
            orders_base
            .filter(order_status='confirmed')
            .annotate(date=trunc_func('buy_now_clicked_at', tzinfo=current_tz))
            .values('date')
            .annotate(count=Count('id'))
        )

        total_map = {
           normalize(item['date']): item['count'] for item in total_orders_qs
        }
        confirmed_map = {item['date']: item['count'] for item in confirmed_qs}
        order_activity_trend = {
            "labels": [str(d) for d in date_list],
            "total_orders": [total_map.get(d, 0) for d in date_list],
            "confirmed_orders": [confirmed_map.get(d, 0) for d in date_list],
        }

        # 2) Order Status Distribution

        status_distribution = (orders_base
            .aggregate(
            pending=Count('id',filter=Q(order_status='pending')),
            confirmed=Count('id',filter=Q(order_status='confirmed')),
            cancelled=Count('id',filter=Q(order_status='cancelled'))
        )
        )

        # 3) Top Products by orders
        order_item_base = (
            OrderItem.objects
            .filter(order__order_status='confirmed'
            )
        )
        
        if start_date:
            order_item_base = order_item_base.filter(
                order__created_at__range=(start_date,end_date)
            )
            

        top_products = (
            order_item_base
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
            order_item_base
            .values('product__category__name')
            .annotate(
                revenue=Sum('total_price'),
                orders=Count('order',distinct=True)
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
        
        
        now = timezone.now()
        last_7_days = now - timedelta(days=7)
        
        
        recent_orders_qs = (
            Order.objects
            .filter(created_at__gte=last_7_days)
            .select_related('customer')
            .annotate(items_count=Count('items'))
            .order_by('-created_at')
        )
        
        # Pagination
        paginator = AdminDashboardRecentOrderPagination()
        page = paginator.paginate_queryset(recent_orders_qs,request)
        
        results=[]
        for order in page:
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
            'from': str(last_7_days.date()) ,
            'to': str(now.date()),
            'recent_orders': results
        }

        return paginator.get_paginated_response(data)
        
        
        