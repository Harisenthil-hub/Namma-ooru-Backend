from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True,max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    image = models.ImageField(upload_to='products/')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    stock = models.PositiveIntegerField(default=0)
    slug = models.SlugField(unique=True,max_length=50)
    offer_badge = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    