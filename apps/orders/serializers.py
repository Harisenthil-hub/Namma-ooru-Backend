from rest_framework import serializers
from django.utils import timezone
from .models import Order, Customer, OrderItem


class AdminOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'product_name',
            'unit_price',
            'quantity',
            'total_price'
        ]


class AdminOrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name")
    phone_no = serializers.CharField(source="customer.phone_no")
    pending_minutes = serializers.SerializerMethodField()
    items = AdminOrderItemSerializer(many=True,read_only=True)
    
    street = serializers.CharField(source='shipping_address.street')
    city = serializers.CharField(source='shipping_address.city')
    pincode = serializers.CharField(source='shipping_address.pincode')
    landmark = serializers.CharField(source='shipping_address.landmark')
    
    class Meta:
        model = Order
        fields = [
            "order_number",
            "order_status",
            "customer_name",
            "phone_no",
            "total_amount",
            "created_at",
            "pending_minutes",
            "items",
            "street",
            "city",
            "pincode",
            'landmark',
        ]

    def get_pending_minutes(self, obj):
        if obj.order_status != "pending":
            return None
        return int((timezone.now() - obj.created_at).total_seconds() / 60)

class AdminCustomerListSerializer(serializers.ModelSerializer):
    total_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_order_at = serializers.DateTimeField()
    
    street = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    landmark = serializers.CharField(read_only=True)
    pincode = serializers.CharField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'phone_no',
            'email',
            'total_orders',
            'total_spent',
            'street',
            'city',
            'landmark',
            'pincode',
            'last_order_at',
            'created_at',
            'last_address',
        ]
