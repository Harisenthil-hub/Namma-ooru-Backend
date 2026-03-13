from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Category, Product


# CATEGORY CACHE CLEAR
@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def clear_category_cache(sender, **kwargs):
    print(3456)
    cache.delete("category_list")
    cache.delete_pattern("products_*")
    cache.delete_pattern("search_suggestions_*")
    


# PRODUCT CACHE CLEAR
@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_product_cache(sender, **kwargs):
    print('dfdfdf')
    cache.delete_pattern("products_*")