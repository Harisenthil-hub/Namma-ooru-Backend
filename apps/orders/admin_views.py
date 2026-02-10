from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q, Count, Sum, Max
from django.core.cache import cache
from datetime import timedelta
from .pagination import AdminOrderPagination


from .models import Order, Customer
from .serializers import AdminOrderListSerializer, AdminCustomerListSerializer


class AdminOrderListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminOrderListSerializer
    pagination_class = AdminOrderPagination

    def get_queryset(self):

        qs = Order.objects.select_related('customer').only(
            'order_number', 'order_status', 'total_amount', 'created_at',
             'customer__name', 'customer__phone_no'
        ).order_by('-created_at')


        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        if status:
            qs = qs.filter(order_status=status)

        if search:
            qs = qs.filter(
                Q(order_number__startswith=search) |
                Q(customer__phone_no__startswith=search)
            )

        return qs


class AdminOrderStatusUpdateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self,request,order_number):
        new_status = request.data.get('status')

        if new_status not in ['confirmed' ,'cancelled']:
            return Response(
                { 'error': 'Invalid Status' },
                status=status.HTTP_400_BAD_REQUEST
            )


        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response(
                { 'error': 'Order not found' },
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = order.order_status

        if old_status == new_status:
            return Response(
                { 'error': 'Order already in this status' },
                status=status.HTTP_400_BAD_REQUEST
            )

        order.order_status = new_status
        order.save(update_fields=['order_status'])

        return Response(
            { 'message': f"Order marked as {new_status}" },
            status=status.HTTP_200_OK
        )


class AdminCustomerListAPIVies(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCustomerListSerializer
    pagination_class = AdminOrderPagination # same Pagination as Order list

    def get_queryset(self):
        search = self.request.query_params.get('search','').strip()
        cache_key = f'admin_customer_list:{search}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        qs = (
            Customer.objects
            .annotate(
                total_orders=Count('orders',distinct=True),
                total_spent=Sum('orders__total_amount'),
                last_order_at=Max('orders__created_at'),
            )
            .order_by('-last_order_at')
        )

        if search:
            qs = qs.filter(
                Q(phone_no__startswith=search) |
                Q(name__istartswith=search)
            )

        result = list(qs)
        cache.set(cache_key,result,timeout=60)

        return result


        