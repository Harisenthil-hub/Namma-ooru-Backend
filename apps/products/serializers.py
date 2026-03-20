from rest_framework import serializers
from .models import Product, Category, ProductVariant
from django.db import transaction
import json
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


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
    
    @method_decorator(cache_page(60 * 5))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


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
            
            variant_objects = []
            for variant in variants_data:
                for key, value in variant.items():
                    if value == '':
                        variant[key] = None
                
                variant_objects.append(
                    ProductVariant(product=product,**variant)
                )
            ProductVariant.objects.bulk_create(variant_objects)
            
        return product
    

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','image','updated_at']
        

class AdminCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'image',
            'is_active',
            'created_at',
            'product_count',
            'updated_at'
        ]
        
class AdminCreateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name','image','is_active']
        
    def validate_name(self,value):
        category_id = self.instance.id if self.instance else None
        if Category.objects.filter(name__iexact=value)\
        .exclude(id=category_id).exists():
            raise serializers.ValidationError("Category already Exists")
        return value