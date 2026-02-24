from rest_framework.generics import ListAPIView, CreateAPIView , RetrieveUpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAdminUser
from .models import Product, ProductVariant, Category
from .serializers import ProductSerializer, ProductVariantSerializer, AdminProductCreateSerializer, AdminCategorySerializer
from .serializers import AdminCreateCategorySerializer
from .pagination import AdminProductPagination, AdminCategoryPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from rest_framework.filters import SearchFilter
from django.db.models import Count
from rest_framework.parsers import MultiPartParser, FormParser


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
        return (
            Category.objects
            .annotate(product_count=Count('products',distinct=True))
            .order_by('-created_at')
        )
        
        
        
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
    parser_classes = [MultiPartParser,FormParser]
    