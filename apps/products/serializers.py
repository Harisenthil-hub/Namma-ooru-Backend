from rest_framework import serializers
from .models import Product, Category, ProductVariant
from django.db import transaction
import json

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'


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


class AdminProductCreateSerializer(serializers.ModelSerializer):
    variants = serializers.CharField(
        required=False,write_only=True
    )
    
    class Meta:
        model = Product
        fields = '__all__'
        
        
    def create(self,validated_data):
        request = self.context.get('request')
        
        variants_data = request.data.get('variants',[])
        
        if isinstance(variants_data,str):
            variants_data = json.loads(variants_data)
            
        
        validated_data.pop('variants',None)
        
        with transaction.atomic():
            product = Product.objects.create(**validated_data)
            
            variant_objects = [
                ProductVariant(product=product,**variant)
                for variant in variants_data
            ]
            
            ProductVariant.objects.bulk_create(variant_objects)
            
        return product
    

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name']