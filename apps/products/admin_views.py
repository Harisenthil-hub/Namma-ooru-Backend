from rest_framework.generics import ListAPIView, CreateAPIView , RetrieveUpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAdminUser
from .models import Product, ProductVariant
from .serializers import ProductSerializer, ProductVariantSerializer
from .pagination import AdminProductPagination


class AdminProductListAPIView(ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    pagination_class = AdminProductPagination

class AdminProductCreateAPIView(CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def perform_create(self, serializer):
        print("FILES:", self.request.FILES)
        serializer.save()

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
    
    
class AdminProductVariantUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = IsAdminUser
    serializer_class = ProductVariantSerializer
    queryset = ProductVariant.objects.all()
    
    
class AdminProductVariantDeleteAPIView(DestroyAPIView):
    permission_classes = IsAdminUser
    queryset = ProductVariant.objects.all()