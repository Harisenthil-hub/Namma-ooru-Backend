from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import Product, Category, ProductVariant
from .serializers import ProductSerializer, CategorySerializer
from apps.orders.models import OrderItem
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.db.models import Count, Prefetch, Q, OuterRef, Exists
from .pagination import UserProductPagination
from rest_framework.filters import SearchFilter
from django.core.cache import cache
# Create your views here.

# This is for Product listing page
class ProductListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = UserProductPagination
    filter_backends = [SearchFilter]
    search_fields = ['name','category__name']
    # queryset = Product.objects.filter(is_active=True)
    
    def get_queryset(self):
        queryset =  Product.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'variants',
                queryset = ProductVariant.objects.filter(is_active=True)
            )
        )
        
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(category__name__icontains=search)
            )
            
        if category:
            queryset = queryset.filter(category_id=category)
            
            
        return (queryset)
    

class HomeProductAPIView(APIView):

    def get(self,request):

        cache_key = 'home_products'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Take only Products are active (Base query)
        base_qs = Product.objects.filter(is_active=True)
        
        # Check if a Product has an active variant (Sub query)
        offer_variant_subquery = ProductVariant.objects.filter(
            product=OuterRef('pk'),
            is_active=True,
            offer_price__gt=0
        )
        
        # Getting Top selling Product Ids (Step 1)
        top_ids = list(
            OrderItem.objects
            .filter(order__order_status='confirmed')
            .values('product_id')
            .annotate(total_orders=Count('id'))
            .order_by('-total_orders')
            .values_list('product_id',flat=True)[:5]
        )
        
        # Fetching Top Products (Step 2)
        products = list(base_qs.filter(id__in=top_ids))
        

        # Fallback --> Offer Products (Step 3)
        if len(products) < 5:
            remaining = 5 - len(products)
            offer_products = (
                base_qs
                .annotate(has_offer=Exists(offer_variant_subquery))
                .filter(has_offer=True)
                .exclude(id__in=[p.id for p in products])
                .order_by('-created_at')[:remaining]
            )
            products.extend(list(offer_products))



        # Fallback --> Latest Products (Step 4)
        if len(products) < 5 :
            remaining = 5 - len(products)
            latest_products = (
                base_qs
                .exclude(id__in=[p.id for p in products])
                .order_by('-created_at')[:remaining]
            )
            products.extend(list(latest_products))


        data = ProductSerializer(products, many=True,context={ 'request':request }).data
        cache.set(cache_key, data, timeout=10)

        return Response(data, status=status.HTTP_200_OK)


class CategoryListAPIView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductSearchSuggestionAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def get(self,request):
        
        keyword = request.query_params.get('q','').strip().lower()
        
        
        if len(keyword)<2:
            return Response([],status=status.HTTP_200_OK)
        
        cache_key = f'search_suggestiosn:{keyword}'
        cached = cache.get(cache_key)
        
        if cached:
            return Response(cached,status=status.HTTP_200_OK)
        
        suggestions = list(
            Product.objects
            .filter(name__icontains=keyword,is_active=True)
            .values_list('name',flat=True)
            .distinct()[:10]
        )
        
        cache.set(cache_key,suggestions,timeout=10)
        return Response(suggestions,status=status.HTTP_200_OK)
        
        
       