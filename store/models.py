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
    
from django.db import models
from django.utils import timezone

class Employee(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    salary = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="active")

    # Running debt balance
    debt_balance = models.IntegerField(default=0)  

    def __str__(self):
        return self.name

    def take_salary(self):
        """
        When employee takes salary, debt is reduced by salary amount.
        If employee has no debt, he just gets his salary.
        """
        if self.debt_balance > 0:
            amount_used = min(self.salary, self.debt_balance)
            self.debt_balance -= amount_used
            self.save()
            EmployeeTransaction.objects.create(
                employee=self,
                type="salary",
                amount=self.salary,
                note=f"Salary taken, {amount_used} used to cover debt."
            )
        else:
            EmployeeTransaction.objects.create(
                employee=self,
                type="salary",
                amount=self.salary,
                note="Salary taken."
            )


class EmployeeTransaction(models.Model):
    TRANSACTION_TYPES = (
        ("debt", "Debt"),
        ("deposit", "Deposit"),
        ("salary", "Salary"),
        ("adjustment", "Adjustment"),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="transactions")
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    channel = models.CharField(max_length=255,default="cash")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update employee debt balance dynamically
        if self.type == "debt":
            self.employee.debt_balance += self.amount
        elif self.type == "deposit":
            self.employee.debt_balance -= self.amount
        # salary doesn't directly affect debt (unless you want to auto-reduce)
        elif self.type == "adjustment":
            self.employee.debt_balance += self.amount
        self.employee.save()

    def __str__(self):
        return f"{self.employee.name} - {self.type} - {self.amount}"

    
 
  
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
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, related_name='products',null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    purchase_price = models.IntegerField(default=0)
    sale_price = models.IntegerField(default=0)
    stock_quantity = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class ProductTrackUpdate(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='updates')
    field_name = models.CharField(max_length=100)  # e.g. 'sale_price', 'stock_quantity'
    productName = models.CharField(max_length=100)  # e.g. 'sale_price', 'stock_quantity'
    userName = models.CharField(max_length=100)  # e.g. 'sale_price', 'stock_quantity'
    old_value = models.CharField(max_length=255, null=True, blank=True)
    new_value = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.field_name} changed on {self.updated_at.strftime('%Y-%m-%d %H:%M')}"
class Bills(models.Model):
    phone = models.CharField(max_length=50, blank=True, null=True)
    balance = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class Sales(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, related_name='products', null=True, db_index=True)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, related_name='salesman', null=True, db_index=True)
    ProductName = models.CharField(max_length=255, db_index=True)
    userName = models.CharField(max_length=255)
    type = models.CharField(max_length=255, default="cash")
    description = models.TextField(blank=True, null=True)
    price_unit = models.FloatField(default=0)
    price_total = models.FloatField(default=0)
    bill = models.ForeignKey(Bills, on_delete=models.SET_NULL, null=True, related_name="sales", db_index=True)
    benefit = models.FloatField(default=0)
    quantity = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    canceled = models.BooleanField(default=False)


class Transaction(models.Model):
    CASH_IN = 'IN'
    CASH_OUT = 'OUT'
    CASH_BETWEEN = 'BETWEEN' #for the inner transaction 
    TRANSACTION_TYPES = [(CASH_IN, 'Cashing In'), (CASH_OUT, 'Cashing Out')]
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES , db_index=True)
    amount = models.FloatField(default=0)
    before = models.FloatField(default=0)
    after = models.FloatField(default=0)
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True , db_index=True)
    user = models.ForeignKey(Users,on_delete=models.SET_NULL, null=True)
    sale = models.ForeignKey(Sales,on_delete=models.SET_NULL, null=True)
    userName = models.CharField(max_length=255)
    channel = models.CharField(max_length=255,default="cash")

class Treasury(models.Model):
    userName = models.CharField(max_length=255)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True)
    balance = models.FloatField(default=0)
    Bankily_balance = models.FloatField(default=0)
    Sedad_balance = models.FloatField(default=0)
    BimBank_balance = models.FloatField(default=0)
    Masrivy_balance = models.FloatField(default=0)
    Click_balance = models.FloatField(default=0)
    last_update = models.DateTimeField(auto_now=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL , null=True)


class Debts(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    balance = models.FloatField(default=0)
    initAmount = models.FloatField(default=0)
    last_update = models.DateTimeField(auto_now=True)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    bill = models.ForeignKey(
        Bills,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="debts"
    )
class SuppliersDebts(models.Model):
    bill = models.JSONField(default=list, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    balance = models.FloatField(default=0)
    initAmount = models.FloatField(default=0)
    last_update = models.DateTimeField(auto_now=True)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supliers"
    )
class SuppliersDebtsPayment(models.Model):
    userName = models.CharField(max_length=255)
    type = models.CharField(max_length=255,default="cash")
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True)
    debt = models.ForeignKey(SuppliersDebts, on_delete=models.SET_NULL, related_name="supp_payments",null=True , db_index=True)  # <-- link to Debts
    balance = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    isDeposit=models.BooleanField(default=False)
    description = models.TextField(max_length=255 ,blank=True, null=True)

class DebtsPayment(models.Model):
    userName = models.CharField(max_length=255)
    description = models.CharField(max_length=255,blank=True, null=True )
    type = models.CharField(max_length=255,default="cash")
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True)
    debt = models.ForeignKey(Debts, on_delete=models.CASCADE, related_name="payments",null=True , db_index=True)  # <-- link to Debts
    balance = models.FloatField(default=0)
    isDeposit=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Deposits(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    balance = models.FloatField(default=0)
    initAmount=models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now=True)
    done=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
class DepositsPayment(models.Model):
    userName = models.CharField(max_length=255)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=255,default="cash")
    description = models.TextField(blank=True, null=True)
    balance = models.FloatField(default=0)
    Deposits = models.ForeignKey(Deposits, on_delete=models.CASCADE, related_name="payments",null=True , db_index=True)  # <-- link to Debts
    created_at = models.DateTimeField(auto_now_add=True)
    isDeposit=models.BooleanField(default=False)

class Backup(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    size = models.TextField(blank=True, null=True)













from django.db import models
from django.core.validators import MinValueValidator
from django.core.serializers.json import DjangoJSONEncoder
import json

class MonthlyExpenses(models.Model):
    """
    Model to track monthly expenses with detailed expense items
    """
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES,
        help_text="Month number (1-12)"
    )
    
    year = models.PositiveIntegerField(
        help_text="Year of the expenses"
    )
    
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Total amount of expenses for the month"
    )
    
    expenses = models.JSONField(
        default=list,
        encoder=DjangoJSONEncoder,
        help_text="List of expense items in JSON format"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Monthly Expense"
        verbose_name_plural = "Monthly Expenses"
        unique_together = ['month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.get_month_display()} {self.year} - ${self.total}"
    
    def save(self, *args, **kwargs):
        # Calculate total from expenses if not provided
        if not self.total and self.expenses:
            self.total = sum(float(expense.get('bill', 0)) for expense in self.expenses)
        super().save(*args, **kwargs)
    
    @property
    def formatted_expenses(self):
        """Return expenses as a nicely formatted string"""
        if not self.expenses:
            return "No expenses"
        
        items = []
        for expense in self.expenses:
            label = expense.get('label', 'Unlabeled')
            amount = expense.get('bill', 0)
            items.append(f"{label}: ${amount}")
        
        return "; ".join(items)
    
    @classmethod
    def get_current_month_expenses(cls):
        """Get expenses for current month"""
        import datetime
        now = datetime.datetime.now()
        return cls.objects.filter(month=now.month, year=now.year).first()
    
    def add_expense(self, label, bill):
        """Helper method to add an expense item"""
        if not isinstance(self.expenses, list):
            self.expenses = []
        
        self.expenses.append({
            'label': label,
            'bill': float(bill)
        })
        self.save()
    
    def remove_expense(self, index):
        """Helper method to remove an expense by index"""
        if isinstance(self.expenses, list) and 0 <= index < len(self.expenses):
            del self.expenses[index]
            self.save()
            return True
        return False
    
    @property
    def expense_categories(self):
        """Get all unique expense categories/labels"""
        if not self.expenses:
            return []
        
        categories = set()
        for expense in self.expenses:
            label = expense.get('label')
            if label:
                categories.add(label)
        
        return list(categories)
    
    @property
    def expenses_by_category(self):
        """Group expenses by category"""
        if not self.expenses:
            return {}
        
        grouped = {}
        for expense in self.expenses:
            label = expense.get('label', 'Uncategorized')
            bill = float(expense.get('bill', 0))
            
            if label in grouped:
                grouped[label].append(bill)
            else:
                grouped[label] = [bill]
        
        return grouped
    
    @property
    def total_by_category(self):
        """Calculate total by category"""
        grouped = self.expenses_by_category
        return {category: sum(bills) for category, bills in grouped.items()}