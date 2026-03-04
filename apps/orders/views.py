from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from decimal import Decimal
from django.utils import timezone


from .models import Customer, Order, OrderItem, Address
from apps.products.models import Product, ProductVariant



# Create your views here.

class CreateOrderAPIView(APIView):
    permission_classes=[AllowAny]

    @transaction.atomic
    def post(self, request):
        data = request.data

        customer_data = data.get('customer')
        address_data = data.get('address')
        items_data = data.get('items')

        if not customer_data or not items_data or not address_data:
            return Response(
                { 'error': 'Customer, address and items are required' },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Customer Handling
        phone = customer_data.get('phone_no')
        
        if not phone:
            return Response(
                {"error": "Primary Phone no is required"},
                status=status.HTTP_400_BAD_REQUEST
            )



        # Get or Create customer
        customer, created = Customer.objects.get_or_create(
            phone_no = phone,
            defaults = {
                'name': customer_data.get('name',''),
                'email': customer_data.get('email'),
                'alternate_phone_no': customer_data.get('alternate_phone_no')
            }
        )
        
        
        
        # If existing customer -> update details
        if not created:
            customer.name = customer_data.get('name',customer.name)
            customer.email = customer_data.get('email',customer.email)
            customer.alternate_phone_no = customer_data.get(
                'alternate_phone_no',
                customer.alternate_phone_no
            )
            customer.save()
            
            
            
        
        # Create or get Address 
        
        street = address_data.get('street','').strip().lower()
        city = address_data.get('city','').strip().lower()
        pincode = address_data.get('pincode','').strip()
        landmark = address_data.get('landmark','').strip().lower()
        
        
        address = Address.objects.filter(
            customer=customer,
            street = street,
            city = city,
            pincode = pincode,
            landmark = landmark 
        ).first()
         
         
        if not address:
            address = Address.objects.create(
                customer=customer,
                street = street,
                city = city,
                pincode = pincode,
                landmark = landmark 
            )

        # Fetch Varianst in Bulk (Optimized)
        variant_ids = [item['variant_id'] for item in items_data]
        
        variants = ProductVariant.objects.filter(
            id__in=variant_ids,
            is_active=True
        ).select_related('product')
        
        variants_map = { v.id: v for v in variants  }
        
        subtotal = Decimal('0.00')
        order_items = []
        
        # Calculate total
        for item in items_data:
            product_id = item.get('product_id')
            variant_id = item.get('variant_id')
            quantity = int(item.get('quantity',1))
            
            variant = variants_map.get(variant_id)
            
            if not variant:
                return Response(
                    {'error': f'Variant {variant_id} not found or inactive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if variant.product_id != product_id:
                return Response(
                    {'error': f'Variant {variant_id} does not belong to Product {product_id}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            # Using Offer Price
            price = (
                variant.offer_price
                if variant.offer_price and variant.offer_price > 0
                else variant.price
            )
            
            line_total = price * quantity
            subtotal += line_total
            
            order_items.append(
                OrderItem(
                    product=variant.product,
                    variant=variant,
                    variant_weight=variant.weight,
                    product_name=variant.product.name,
                    unit_price=price,
                    quantity=quantity,
                    total_price=line_total
                )
            )


        tax = Decimal('0.00') # tax may change
        total_amount = subtotal + tax

        # Create order
        order = Order.objects.create(
            customer=customer,
            shipping_address=address,
            order_status='pending', # later can be changed
            sub_total=subtotal,
            tax=tax,
            total_amount=total_amount,
            buy_now_clicked_at=timezone.now()
        )


        # Generate order number
        order.order_number = f"ORD-{1000 + order.id}"
        order.save(update_fields=['order_number'])

        # Attach order to items
        for item in order_items:
            item.order = order
            
        OrderItem.objects.bulk_create(order_items)

       
        return Response(
            {
                "message": "Order created successfully",
                "order_number": order.order_number,
                "total_amount": str(order.total_amount)
            },status=status.HTTP_201_CREATED
        )


