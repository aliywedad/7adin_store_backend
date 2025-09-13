from django.db import models


   
   
class Users(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=False)
    password = models.CharField(max_length=255, blank=True, null=False)
    token = models.CharField(max_length=255, blank=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    roles = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, default="active")


    def __str__(self):
        return self.name
    
 
    
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products',null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Sales(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='products',null=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='salesman',null=True)
    ProductName = models.CharField(max_length=255)
    userName = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price_unit = models.DecimalField(max_digits=10, decimal_places=2)
    price_total = models.DecimalField(max_digits=10, decimal_places=2)
    benefit = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    
class Treasury(models.Model):
    userName = models.CharField(max_length=255)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=True)
    amount_sent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    before = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_update = models.DateTimeField(auto_now=True)
    
class Transaction(models.Model):
    CASH_IN = 'IN'
    CASH_OUT = 'OUT'
    TRANSACTION_TYPES = [(CASH_IN, 'Cashing In'), (CASH_OUT, 'Cashing Out')]

    treasury = models.ForeignKey(Treasury, on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True)
    userName = models.CharField(max_length=255)
