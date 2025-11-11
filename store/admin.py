from django.contrib import admin
from .models import Users, Supplier, Product, Sales, Transaction, Treasury

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone','roles', 'email', 'status', 'created_at')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('status',)
    ordering = ('-created_at',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contact_name', 'phone', 'email', 'address', 'created_at')
    search_fields = ('name', 'contact_name', 'email')
    ordering = ('-created_at',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'supplier', 'purchase_price', 'sale_price', 'stock_quantity', 'created_at')
    search_fields = ('name',)
    list_filter = ('supplier',)
    ordering = ('-created_at',)

@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = ('id', 'ProductName', 'userName', 'product', 'user', 'quantity', 'price_unit', 'price_total', 'benefit', 'created_at')
    search_fields = ('ProductName', 'userName')
    list_filter = ('user', 'product')
    ordering = ('-created_at',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'amount', 'before', 'after', 'reason', 'userName', 'user', 'sale', 'created_at')
    search_fields = ('reason', 'userName')
    list_filter = ('type',)
    ordering = ('-created_at',)

@admin.register(Treasury)
class TreasuryAdmin(admin.ModelAdmin):
    list_display = ('id', 'userName', 'user', 'balance', 'last_update', 'transaction')
    search_fields = ('userName',)
    ordering = ('-last_update',)
