from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet)
router.register(r'sales', SalesViewSet)
router.register(r'users', UserViewSet)
router.register(r'Treasury', TreasuryViewSet)
router.register(r'Transactions', TransactionViewSet)

urlpatterns = [
    
    path("login/", login, name="login"),
    path("getUserInfoById/", getUserInfoById, name="getUserInfoById"),
    path('api/', include(router.urls)),
]