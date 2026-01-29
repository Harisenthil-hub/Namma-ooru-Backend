from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from decimal import Decimal
from django.utils import timezone


from .models import Customer, Order, OrderItem
from apps.products.models import Product



# Create your views here.

class CreateOrderAPIView(APIView):
    permission_classes=[AllowAny]

    @transaction.atomic
    def post(self, request):
        data = request.data

        customer_data = data.get('customer')
        items_data = data.get('items')

        if not customer_data or not items_data:
            return Response(
                { 'error': 'Customer and items are required' },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or Create customer
        customer, _ = Customer.objects.get_or_create(
            phone_no = customer_data['phone_no'],
            defaults = {
                'name': customer_data.get('name',''),
                'email': customer_data.get('email')
            }
        )

        subtotal = Decimal('0.00')

        # Calculate subtotal
        products_map = {}
        for item in items_data:
            product = Product.objects.get(id=item['product_id'])
            quantity = int(item['quantity'])
            subtotal += product.price * quantity
            products_map[item['product_id']] = product


        tax = Decimal('0.00') # tax may change
        total_amount = subtotal + tax

        # Create order
        order = Order.objects.create(
            customer=customer,
            order_status='pending', # later can be changed
            sub_total=subtotal,
            tax=tax,
            total_amount=total_amount,
            buy_now_clicked_at=timezone.now()
        )


        # Generate order number
        order.order_number = f"ORD-{1000 + order.id}"
        order.save()


        # Create order items
        for item in items_data:
            product = products_map[item['product_id']]
            quantity = int(item['quantity'])


            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=quantity,
                total_price=product.price * quantity
            )

        return Response(
            {
                "message": "Order created successfully",
                "order_number": order.order_number,
                "total_amount": str(order.total_amount)
            },status=status.HTTP_201_CREATED
        )


