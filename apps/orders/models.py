from django.db import models

# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone_no = models.CharField(max_length=15,unique=True,blank=False,db_index=True)
    email = models.EmailField(max_length=100,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.phone_no}"
    

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('cancelled','Cancelled')
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    order_number = models.CharField(max_length=30,unique=True,db_index=True)
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending',
        db_index=True,

    )

    sub_total = models.DecimalField(max_digits=10,decimal_places=2)
    tax = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2)

    buy_now_clicked_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)
    update_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.order_number


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT
    )

    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10,decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10,decimal_places=2)


    def __str__(self):
        return f"{self.product_name} ({self.quantity})"
    