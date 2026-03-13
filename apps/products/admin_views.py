from rest_framework.generics import ListAPIView, CreateAPIView , RetrieveUpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAdminUser
from .models import Product, ProductVariant, Category
from .serializers import ProductSerializer, ProductVariantSerializer, AdminProductCreateSerializer, AdminCategorySerializer
from .serializers import AdminCreateCategorySerializer, CategorySerializer
from .pagination import AdminProductPagination, AdminCategoryPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from rest_framework.filters import SearchFilter
from django.db.models import Count, Q
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .exports import generate_product_export
from django.utils.dateparse import parse_date
from datetime import timedelta
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from django.utils.timezone import now


class AdminProductListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    pagination_class = AdminProductPagination
    filter_backends = [SearchFilter]
    search_fields = ['name','variants__weight']
    
    def get_queryset(self):
        
        queryset = Product.objects.all().prefetch_related(
            'category',
            'variants',
        ).distinct()
        
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        
        return queryset
   

class AdminProductCreateAPIView(CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminProductCreateSerializer
    queryset = Product.objects.all()

class AdminProductUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = 'id'

class AdminProductDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = 'id'
    
    
class AdminProductVariantCreateAPIView(CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductVariantSerializer
    
    
# class AdminProductVariantUpdateAPIView(RetrieveUpdateAPIView):
#     permission_classes = [IsAdminUser]
#     serializer_class = ProductVariantSerializer
#     queryset = ProductVariant.objects.all()
#     lookup_field = 'pk'


class AdminProductVariantUpdateAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def patch(self,request,product_id):
        variants_data = request.data.get('variants',[])
        
        
        if not variants_data:
            return Response({ 'error': 'No variants provided' },status=status.HTTP_400_BAD_REQUEST)
        
        variant_ids = [v.get('id') for v in variants_data if v.get('id')]
        
        variants = ProductVariant.objects.filter(
            id__in = variant_ids,
            product_id = product_id
        )
        
        variant_dict = {variant.id: variant for variant in variants}
        
        
        updated_variants = []
        not_found_ids = []
        
        with transaction.atomic():
            for variant_data in variants_data:
                variant_id = variant_data.get('id')
                variant = variant_dict.get(variant_id)
                
                if not variant:
                    not_found_ids.append(variant)
                    continue
                
                
                serializer = ProductVariantSerializer(variant,data=variant_data,partial=True)
                
                if serializer.is_valid():
                    serializer.save()
                    updated_variants.append(serializer.data)
                else:
                    return Response({
                        "error": "Validation failed",
                        "details": serializer.errors,
                        "data_received": variant_data
                    },status=status.HTTP_400_BAD_REQUEST)
                
                
        return Response({
            'message': 'Variants updated Successfully',
            'updated_count': len(updated_variants),
            'not_found_ids': not_found_ids,
            'variants': updated_variants
        },status=status.HTTP_200_OK)
    
        
            
    
class AdminProductVariantDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = ProductVariant.objects.all()
    
    
class AdminCategoryListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCategorySerializer
    pagination_class = AdminCategoryPagination
    
    def get_queryset(self):
        
        search = self.request.query_params.get('search','').strip()
        qs = (
            Category.objects
            .annotate(product_count=Count('products',distinct=True))
            .order_by('-created_at')
        )
        
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
            )
            
        return qs
        
        
        
class AdminCreatCategoryAPIView(CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCreateCategorySerializer
    queryset = Category.objects.all()
    
    #Required for image upload
    parser_classes = [MultiPartParser,FormParser]
    
    
class AdminUpdateCategoryAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCreateCategorySerializer
    queryset = Category.objects.all()
    parser_classes = [MultiPartParser,FormParser,JSONParser]
    
    
class AdminProductExportAPIView(APIView):
    permission_classes = [IsAdminUser]
    renderer_classes = [JSONRenderer]
    
    def get(self,request):
        
        filter_type = request.GET.get("filter_type")
        date = request.GET.get('date')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        quick_filter = request.GET.get('filter')
        variant_mode = request.GET.get('variant_mode','all')
        include_summary = request.GET.get('include_summary','false').lower() == 'true'
        
        products = Product.objects.select_related(
            'category',
        ).prefetch_related('variants')
        
       
        if filter_type:
            variant_mode = 'all'
        elif date:
            products = products.filter(
                updated_at__date=parse_date(date)
            )
        elif start_date and end_date:
            products = products.filter(
                updated_at__date__gte=parse_date(start_date),
                updated_at__date__lte=parse_date(end_date)
            )
        elif quick_filter:
            today = now().date()
            if quick_filter == 'today':
                products = products.filter(updated_at__date=today)
            elif quick_filter == 'yesterday':
                products = products.filter(updated_at__date=today - timedelta(days=1))
            elif quick_filter == 'last_7_days':
                products = products.filter(updated_at__date__gte=today - timedelta(days=7))
                
                
        products = products.order_by('-updated_at')
        
        wb = generate_product_export(products,request,variant_mode,include_summary)
        
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response['Content-Disposition'] = 'attachment; filename="products_export.xlsx"'
        
        wb.save(response)
        return response
  
class AdminCategoryListProductPageAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer      