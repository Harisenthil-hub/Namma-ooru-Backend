from rest_framework.generics import ListAPIView, CreateAPIView , RetrieveUpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAdminUser
from .models import Product
from .serializers import ProductSerializer


class AdminProductListAPIView(ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

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