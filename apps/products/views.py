from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import Product
from .serializers import ProductSerializer
from apps.orders.models import OrderItem
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.db.models import Count

# Create your views here.

# This is for Product listing page
class ProductListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(is_active=True)


class HomeProductAPIView(APIView):

    def get(self,request):

        cache_key = 'home_products'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)


        top_products_ids = list(
            OrderItem.objects
            .filter(order__order_status='confirmed')
            .values('product_id')
            .annotate(orders=Count('id'))
            .order_by('-orders')
            .values_list('product_id',flat=True)[:4]
        )

        products = list(
            Product.objects.filter(id__in=top_products_ids, is_active=True)
        )

        # Fallback --> Offer Products
        if len(products) < 4:
            remaining = 4 - len(products)
            offer_products = (
                Product.objects.filter(is_active=True, offer_badge=True)
                .exclude(id__in=[p.id for p in products])
                .order_by('-created_at')[:remaining]
            )
            products.extend(list(offer_products))

        # Fallback --> Latest Products
        if len(products) < 4 :
            remaining = 4 - len(products)
            latest_products = (
                Product.objects
                .filter(is_active=True)
                .exclude(id__in=[p.id for p in products])
                .order_by('created_at')[:remaining]
            )
            products.extend(list(latest_products))


        data = ProductSerializer(products, many=True).data
        cache.set(cache_key, data, timeout=10)

        return Response(data, status=status.HTTP_200_OK)




