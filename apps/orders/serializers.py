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
            'total_price',
            'variant_weight'
        ]


class AdminOrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name")
    phone_no = serializers.CharField(source="customer.phone_no")
    alternate_phone_no = serializers.CharField(source="customer.alternate_phone_no")
    pending_minutes = serializers.SerializerMethodField()
    items = AdminOrderItemSerializer(many=True,read_only=True)
    
    street = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()
    landmark = serializers.SerializerMethodField()
    
    def get_street(self, obj):
        if obj.shipping_address:
            return obj.shipping_address.street
        return None

    def get_city(self, obj):
        if obj.shipping_address:
            return obj.shipping_address.city
        return None

    def get_pincode(self, obj):
        if obj.shipping_address:
            return obj.shipping_address.pincode
        return None

    def get_landmark(self, obj):
        if obj.shipping_address:
            return obj.shipping_address.landmark
        return None
    
    class Meta:
        model = Order
        fields = [
            "order_number",
            "order_status",
            "customer_name",
            "phone_no",
            "alternate_phone_no",
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
