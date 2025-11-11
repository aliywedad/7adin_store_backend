from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .backup import *

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet)
router.register(r'sales', SalesViewSet)
router.register(r'users', UserViewSet)
router.register(r'treasury', TreasuryViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'debts', DebtsViewSet)
router.register(r'debtsPayment', DebtsPaymentViewSet)
router.register(r'depositsPayment', DepositsPaymentViewSet)
router.register(r'deposit', DepositsViewSet)
router.register(r'bills', BillsViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'SuppliersDebts', SuppliersDebtsViewSet)
router.register(r'SuppliersDebtsPayment', SuppliersDebtsPaymentViewSet)
router.register(r'EmployeeTransaction', EmployeeTransactionViewSet)
router.register(r'product-updates', ProductTrackUpdateViewSet, basename='product-updates')


urlpatterns = [
    
    path("send_backup/", send_backup, name="send_backup"),
    path("sales_summary_by_day/", sales_summary_by_day, name="sales_summary_by_day"),
    
    path("hello/", hello, name="hello"),
    path("login/", login, name="login"),
    path("transfer_Between/", transfer_Between, name="transfer_Between"),
    
    path("addEmployeeTrans/", addEmployeeTrans, name="addEmployeeTrans"),
    
    path("last_treasury/", last_treasury, name="last_treasury"),
    path("get_employee_transactions/", get_employee_transactions, name="get_employee_transactions"),
    
    path("getUserInfoById/", getUserInfoById, name="getUserInfoById"),
    path("registerSales/", registerSales, name="registerSales"),
    path("filter_sales/", filter_sales, name="filter_sales"),
    path("registerSales_debt/", registerSales_debt, name="registerSales_debt"),
    path("deposit_to_treasury/", deposit_to_treasury, name="deposit_to_treasury"),
    path("getPaymentByDebt/", getPaymentByDebt, name="getPaymentByDebt"),
    path("getPaymentByDeposits/", getPaymentByDeposits, name="getPaymentByDeposits"),
    path("CancelSale/", CancelSale, name="CancelSale"),
    
    path("get_transactions/", get_transactions, name="get_transactions"),
    path("add_products/", add_products, name="add_products"),
    path("last_backup/", last_backup, name="last_backup"),
    path("sales_stats/", sales_stats, name="sales_stats"),
    path("get_total_supplires_balance_balance/", get_total_supplires_balance_balance, name="get_total_supplires_balance_balance"),
    path("get_total_deposits_balance/", get_total_deposits_balance, name="get_total_deposits_balance"),
    path("get_total_debts_balance/", get_total_debts_balance, name="get_total_debts_balance"),
    
    path("getPaymentBySupplierDebt/", getPaymentBySupplierDebt, name="getPaymentBySupplierDebt"),
    
    
    
    path('api/', include(router.urls)),
]
