from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q, Count, Sum, Max, Prefetch, OuterRef, Subquery
from django.core.cache import cache
from datetime import timedelta
from .pagination import AdminOrderPagination
from .utils import get_filtered_orders, get_admin_customer_queryset


from .models import Order, Customer, OrderItem, Address
from .serializers import AdminOrderListSerializer, AdminCustomerListSerializer


class AdminOrderListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminOrderListSerializer
    pagination_class = AdminOrderPagination

    def get_queryset(self):
        
        return get_filtered_orders(self.request)


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


class AdminCustomerListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCustomerListSerializer
    pagination_class = AdminOrderPagination # same Pagination as Order list

    def get_queryset(self):
        
        return get_admin_customer_queryset(self.request)
        
        '''
            search = self.request.query_params.get('search','').strip()
            print(search)
            
            latest_address = Address.objects.filter(
                customer=OuterRef('pk')
            ).order_by('-created_at')
            
            qs = (
                Customer.objects
                .annotate(
                    total_orders=Count('orders',distinct=True),
                    total_spent=Sum('orders__total_amount'),
                    last_order_at=Max('orders__created_at'),
                    
                    street = Subquery(latest_address.values('street')[:1]),
                    city = Subquery(latest_address.values('city')[:1]),
                    landmark = Subquery(latest_address.values('landmark')[:1]),
                    pincode = Subquery(latest_address.values('pincode')[:1]),
                )
                .order_by('-last_order_at')
            )
            

            if search:
                qs = qs.filter(
                    Q(phone_no__icontains=search) |
                    Q(name__icontains=search) |
                    Q(addresses__city__icontains=search)
                )
                print(qs)

            return qs  
        '''
        
       

        