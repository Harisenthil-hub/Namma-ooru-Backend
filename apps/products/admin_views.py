from rest_framework.generics import CreateAPIView , RetrieveUpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAdminUser
from .models import Product
from .serializers import ProductSerializer


class AdminProductCreateAPIView(CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

class AdminProductUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = 'slug'

class AdminProductDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = 'slug'