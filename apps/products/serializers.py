from rest_framework import serializers
from .models import Product, Category, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'
        
    def validate(self,data):
        product_id = data.get('product_id')
        weight = data.get('weight')
        
        if ProductVariant.objects.filter(product_id=product_id,weight=weight).exists():
            raise serializers.ValidationError("Variant already exists for this weight")
        
        return data


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name',read_only=True)
    # image_url = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True,read_only=True)
    class Meta:
        model = Product
        fields = '__all__'

    # def get_image_url(self, obj):
    #     request = self.context.get('request')
    #     if obj.image:
    #         return request.build_absolute_uri(obj.image.url)
    #     return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name']