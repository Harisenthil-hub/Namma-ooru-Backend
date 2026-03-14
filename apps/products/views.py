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
from django.db.models import Count, Prefetch, Q, OuterRef, Exists, Case, When, IntegerField, Value, Exists
from .pagination import UserProductPagination
from rest_framework.filters import SearchFilter
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
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
        
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        
        
        cache_key = f'products_{search or 'all'}_{category or 'all'}'
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            return cached_queryset
        queryset =  Product.objects.filter(
            is_active=True,
            category__is_active=True,
            variants__is_active=True
            ).select_related('category').prefetch_related(
            Prefetch(
                'variants',
                queryset = ProductVariant.objects.filter(is_active=True)
            )
        ).distinct()
        
        
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(category__name__icontains=search)
            )
            
        if category:
            queryset = queryset.filter(category_id=category)
            
        cache.set(cache_key, queryset, timeout=60*5)  # 5 minutes
        
        return (queryset)
    

class HomeProductAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self,request):

        cache_key = 'home_products'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Take only Products are active (Base query)
        base_qs = Product.objects.filter(
            is_active=True,
            category__is_active=True,
            variants__is_active=True
        ).prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True)
            )
        ).distinct()
        
        # Check if a Product has an active variant (Sub query)
        offer_variant_subquery = ProductVariant.objects.filter(
            product=OuterRef('pk'),
            is_active=True,
            offer_price__gt=0
        )
        
        # Getting Top selling Product Ids (Step 1)
        top_ids = list(
            OrderItem.objects
            .filter(order__order_status='confirmed',product__is_active=True)
            .values('product_id')
            .annotate(total_orders=Count('product_id'))
            .order_by('-total_orders')
            .values_list('product_id',flat=True)[:5]
        )
        
        # Fetching Top Products (Step 2)
        products = list(base_qs.filter(id__in=top_ids))
        
        existing_ids = {p.id for p in products}
        # Fallback --> Offer Products (Step 3)
        if len(products) < 5:
            remaining = 5 - len(products)
            offer_products = (
                base_qs
                .annotate(has_offer=Exists(offer_variant_subquery))
                .filter(has_offer=True)
                .exclude(id__in=existing_ids)
                .order_by('-created_at')[:remaining]
            )
            products.extend(list(offer_products))
            existing_ids.update(p.id for p in offer_products)


        # Fallback --> Latest Products (Step 4)
        if len(products) < 5 :
            remaining = 5 - len(products)
            latest_products = (
                base_qs
                .exclude(id__in=existing_ids)
                .order_by('-created_at')[:remaining]
            )
            products.extend(list(latest_products))


        data = ProductSerializer(products, many=True,context={ 'request':request }).data
        cache.set(cache_key, data, timeout=(60*5))

        return Response(data, status=status.HTTP_200_OK)


class CategoryListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    
    def list(self, request, *args, **kwargs):
        cache_key = "category_list"

        data = cache.get(cache_key)
        if data:
            return Response(data)

        queryset = Category.objects.filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)

        cache.set(cache_key, serializer.data, timeout=3600)

        return Response(serializer.data)


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
            .filter(name__icontains=keyword,is_active=True,category__is_active=True)
            .values_list('name',flat=True)
            .distinct()[:10]
        )
        
        cache.set(cache_key,suggestions,timeout=60*5)
        return Response(suggestions,status=status.HTTP_200_OK)


class DealsProductListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = UserProductPagination
    filter_backends = [SearchFilter]
    search_fields = ['name','category__name']
    
    
    def get_queryset(self):
        
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        
        
        cache_key = f'products_deals_{search}_{category}'
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            return cached_queryset
        
        # offer_variants = ProductVariant.objects.filter(
        #     product=OuterRef('pk'),
        #     is_active=True,
        #     offer_price__isnull=False
        # )
        
        # queryset = Product.objects.filter(
        #     is_active=True,
        #     variants__is_active=True # ensuring active products
        # ).annotate(
        #     has_offer=Exists(offer_variants)
        # ).prefetch_related(
        #     Prefetch(
        #         'variants',
        #         queryset=ProductVariant.objects.filter(is_active=True)
        #     )
        # ).order_by('-has_offer','-created_at').distinct() # offers first
        
        
        queryset = (
            Product.objects.filter(
                is_active=True,
                is_deals=True,
                category__is_active=True,
                variants__is_active=True
            )
            .select_related('category')
            .prefetch_related(
                Prefetch(
                    'variants',
                    queryset=ProductVariant.objects.filter(is_active=True)
                )
            )
            .order_by('-created_at')
            .distinct()
        )
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(category__name__icontains=search)
            )
            
        if category:
            queryset = queryset.filter(category_id=category)
        
        cache.set(cache_key, queryset, timeout=60*5)  # 5 minutes
        
        return queryset
        
       