from rest_framework import serializers
from .models import *

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'
        
        
class SalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales
        fields = '__all__'
class TreasurySerializer(serializers.ModelSerializer):
    class Meta:
        model = Treasury
        fields = '__all__'
        
class BackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Backup
        fields = '__all__'
        
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        

class BillsSerializer(serializers.ModelSerializer):
    sales = SalesSerializer(many=True, read_only=True)  # nested

    class Meta:
        model = Bills
        fields = '__all__'  # هذا بيرجع كل الحقول + المبيعات
class DebtsSerializer(serializers.ModelSerializer):
    bill = BillsSerializer(read_only=True)  # full details
    bill_id = serializers.PrimaryKeyRelatedField(
        queryset=Bills.objects.all(),
        source='bill',
        write_only=True
        ,        required=False,    # not required
        allow_null=True    # can be null
    )
    class Meta:
        model = Debts
        fields = '__all__'
class DebtsPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtsPayment
        fields = '__all__'
        
class DepositsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposits
        fields = '__all__'
        
class DepositsPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositsPayment
        fields = '__all__'
        
        
class SuppliersDebtsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuppliersDebts
        fields = '__all__'
        

class SuppliersDebtsPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuppliersDebtsPayment
        fields = '__all__'
        
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        
class EmployeeTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeTransaction
        fields = '__all__'
        
class ProductTrackUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTrackUpdate
        fields = '__all__'