import random
import string

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from store.permissions import HasTokenPermission
from .models import Supplier, Product, Users
from .serializers import *
     
from decimal import Decimal, InvalidOperation
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction as db_transaction
from .models import Users, Treasury, Transaction
from .backup import *
from django.utils.timezone import now
from django.db.models import Sum, Count

from rest_framework.decorators import api_view ,permission_classes
import hashlib
from datetime import timedelta
def hash(password: str) -> str:
    md5_hash = hashlib.md5()
    md5_hash.update(password.encode('utf-8'))
    return md5_hash.hexdigest()




from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from django.db.models import Sum
from .models import Sales
from .serializers import SalesSerializer

@api_view(['POST'])
def filter_sales(request):
    product_id = request.data.get("product", 0)
    date_from = request.data.get("date_from", "")
    date_to = request.data.get("date_to", "")

    sales = Sales.objects.all().order_by('-created_at')

    # Filter by product if provided and not 0
    if product_id and int(product_id) != 0:
        prod=Product.objects.filter(id=product_id).first()
        sales = sales.filter(product=prod)

    # Filter by date range if both exist
    if date_from and date_to:
        try:
            from_date = parse_date(date_from)
            to_date = parse_date(date_to)

            # auto-swap if user reverses dates
            if from_date and to_date and from_date > to_date:
                from_date, to_date = to_date, from_date

            if from_date and to_date:
                sales = sales.filter(created_at__date__range=[from_date, to_date])
        except Exception as e:
            return Response({"status": False, "error": str(e)})

    # Aggregate totals
    totals = sales.aggregate(
        total_price=Sum("price_total") or 0,
        total_benefit=Sum("benefit") or 0
    )

    serializer = SalesSerializer(sales, many=True)
    return Response({
        "status": True,
        "results": serializer.data,
        "total_price": totals["total_price"] or 0,
        "total_benefit": totals["total_benefit"] or 0
    })


@api_view(["GET"])
def sales_stats(request):
    today = now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)

    # 1. Today's sales count
    today_sales_count = Sales.objects.filter(created_at__date=today, canceled=False).count()

    # 2. Today's total benefits
    today_sales = Sales.objects.filter(created_at__date=today, canceled=False).aggregate(
        total_benefit=Sum("benefit"),
        total_amount=Sum("price_total")
    )
    today_benefits=today_sales["total_benefit"] or 0
    total_amount=today_sales["total_amount"] or 0

    # 3. Most sold product this week
    most_sold_product = (
        Sales.objects.filter(
            created_at__date__range=[start_of_week, end_of_week],
            canceled=False
        )
        .values("product__id", "ProductName")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")
        .first()
    )

    data = {
        "today_sales_count": today_sales_count,
        "today_total_benefits": today_benefits,
        "today_amount":total_amount,
        "most_sold_product_this_week": most_sold_product
        if most_sold_product else None,
    }

    return Response(data, status=status.HTTP_200_OK)
    
    
    

@api_view(['POST'])
@permission_classes([HasTokenPermission])
def get_transactions(request):
    try:
        type = request.data.get("type")
        ten_days_ago = timezone.now() - timedelta(days=10)

        # Base queryset: only transactions from the last 10 days
        if type and type != "all":
            transactions = Transaction.objects.filter(
                channel=type,
                created_at__gte=ten_days_ago
            ).order_by('-created_at')
        else:
            transactions = Transaction.objects.filter(
                created_at__gte=ten_days_ago
            ).order_by('-created_at')

        serializer = TransactionSerializer(transactions, many=True)
        return Response(
            {
                "type": type,
                "status": True,
                "message": "done",
                "transactions": serializer.data
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "status": False,
                "error": str(e),
            },
            status=status.HTTP_400_BAD_REQUEST
        )


from django.db.models.functions import TruncDate

@api_view(['GET'])
@permission_classes([HasTokenPermission])  # optional
def sales_summary_by_day(request):
    """
    🔹 Endpoint: /sales/summary/
    Returns total benefit, number of sales, and total amount grouped by day.
    """
    try:
        data = (
            Sales.objects.filter(canceled=False)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(
                total_benefit=Sum('benefit'),
                total_sales=Count('id'),
                total_amount=Sum('price_total'),
            )
            .order_by('-day')
        )

        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
     
    
@api_view(["POST"])
def transfer_Between(request):
    """
    تحويل مبلغ بين الأرصدة داخل الخزنة
    البيانات المطلوبة:
    {
        "user": 1,
        "from_balance": "Bankily_balance",
        "to_balance": "Sedad_balance",
        "amount": 500
    }
    """
    user_id = int(request.data.get("user"))
    from_balance = request.data.get("from_balance")
    to_balance = request.data.get("to_balance")
    amount = int(request.data.get("amount"))
    user=Users.objects.get(id=user_id)
 
    try:
        treasury = Treasury.objects.latest('last_update')
    except Treasury.DoesNotExist:
        return Response({"error": "الخزنة غير موجودة"}, status=status.HTTP_404_NOT_FOUND)

    valid_fields = [
        "balance",
        "Bankily_balance",
        "Sedad_balance",
        "BimBank_balance",
        "Masrivy_balance",
        "Click_balance"
    ]
    if from_balance not in valid_fields or to_balance not in valid_fields:
        return Response({"error": "حقول الأرصدة غير صحيحة"}, status=status.HTTP_400_BAD_REQUEST)

    if from_balance == to_balance:
        return Response({"error": "لا يمكن التحويل إلى نفس الرصيد"}, status=status.HTTP_400_BAD_REQUEST)

    amount = int(amount)
    if getattr(treasury, from_balance) < amount:
        return Response({"error": "الرصيد غير كافٍ في الحساب المرسل"}, status=status.HTTP_400_BAD_REQUEST)

    # إنشاء المعاملة قبل التغيير
    before_from = getattr(treasury, from_balance)
    before_to = getattr(treasury, to_balance)

    # تنفيذ التحويل
    setattr(treasury, from_balance, before_from - amount)
    setattr(treasury, to_balance, before_to + amount)
    treasury.save()

    # إنشاء سجل المعاملة
    reason_ar = f"تحويل مبلغ {amount} من {from_balance.replace('_balance','')} إلى {to_balance.replace('_balance','')}"
    Transaction.objects.create(
        type=Transaction.CASH_BETWEEN,
        amount=amount,
        before=before_from,
        after=getattr(treasury, from_balance),
        reason=reason_ar,
        user=user,
        userName=treasury.userName,
        channel=f"{from_balance} → {to_balance}"
    )

    return Response({
        "message": reason_ar,
        "treasury": {
            "id": treasury.id,
            "userName": treasury.userName,
            "balance": treasury.balance,
            "Bankily_balance": treasury.Bankily_balance,
            "Sedad_balance": treasury.Sedad_balance,
            "BimBank_balance": treasury.BimBank_balance,
            "Masrivy_balance": treasury.Masrivy_balance,
            "Click_balance": treasury.Click_balance,
        }
    }, status=status.HTTP_200_OK)

 
 
 
    
@api_view(['GET'])
@permission_classes([HasTokenPermission])
def last_treasury(request):
    try:
        last_record = Treasury.objects.latest('last_update')  # get last by last_update
        serializer = TreasurySerializer(last_record)
        return Response(serializer.data)
    except Treasury.DoesNotExist:
        return Response({"detail": "No treasury records found."}, status=404)
    

@api_view(['GET'])
@permission_classes([HasTokenPermission])
def last_backup(request):
    try:
        last_record = Backup.objects.latest('created_at')  # get last by last_update
        serializer = BackupSerializer(last_record)
        return Response(serializer.data)
    except Treasury.DoesNotExist:
        return Response({"detail": "No treasury records found."}, status=404)
    
    
    
@api_view(["POST"])
def login(request):
    
    identifier = request.data.get("identifier")  # يمكن أن يكون بريد أو هاتف
    password = request.data.get("password")
    

    if not identifier or not password:
        return Response(
            {"message": "البريد الإلكتروني أو رقم الهاتف وكلمة المرور مطلوبان"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if identifier.isdigit() and len(identifier) == 8:  
            # تسجيل الدخول بالهاتف
            user = Users.objects.get(phone=identifier)
        else:
            # تسجيل الدخول بالبريد
            user = Users.objects.get(email=identifier)
    except Users.DoesNotExist:
        return Response(
            {"message": "المستخدم غير موجود"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    hashed_pass=hash(password)

    if user.password != hashed_pass:   
        return Response(
            {"message": "كلمة المرور غير صحيحة"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return Response(
        {
            "message": "تم تسجيل الدخول بنجاح",
            
            "user": {
                "id": user.id,
                "name": user.name,
                "token": user.token,
                "email": user.email,
                "phone": user.phone,
                "roles": user.roles
            }
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([HasTokenPermission])
def getPaymentByDeposits(request):
    deposit_id = request.data.get("id")
    if not deposit_id:
        return Response(
            {"message": "deposit_id id is not provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        deposit = Deposits.objects.get(id=deposit_id)
    except Deposits.DoesNotExist:
        return Response(
            {"message": "deposit not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get payments related to this debt
    depost_payments = DepositsPayment.objects.filter(Deposits_id=deposit).order_by('-created_at')
    serializer = DepositsPaymentSerializer(depost_payments, many=True)
    depositSerializer=DepositsSerializer(deposit)
    
    return Response(
        {"payments": serializer.data,
         "deposit":depositSerializer.data},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([HasTokenPermission])
def getPaymentByDebt(request):
    debt_id = request.data.get("id")
    if not debt_id:
        return Response(
            {"message": "Debt id is not provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        debt = Debts.objects.get(id=debt_id)
    except Debts.DoesNotExist:
        return Response(
            {"message": "Debt not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get payments related to this debt
    debts_payments = DebtsPayment.objects.filter(debt=debt).order_by('-created_at')
    serializer = DebtsPaymentSerializer(debts_payments, many=True)
    debtsSerializer=DebtsSerializer(debt)
    
    return Response(
        {"payments": serializer.data,
         "debt":debtsSerializer.data},
        status=status.HTTP_200_OK
    )
@api_view(["POST"])
@permission_classes([HasTokenPermission])
def getPaymentBySupplierDebt(request):
    debt_id = request.data.get("id")
    if not debt_id:
        return Response(
            {"message": "Debt id is not provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        debt = SuppliersDebts.objects.get(id=debt_id)
    except Debts.DoesNotExist:
        return Response(
            {"message": "Debt not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get payments related to this debt
    debts_payments = SuppliersDebtsPayment.objects.filter(debt=debt).order_by('-created_at')
    serializer = SuppliersDebtsPaymentSerializer(debts_payments, many=True)
    debtsSerializer=SuppliersDebtsSerializer(debt)
    
    return Response(
        {"payments": serializer.data,
         "debt":debtsSerializer.data},
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
def hello(request):
    return Response(
        {"message": "hello"},
        status=status.HTTP_200_OK
    )

 



@api_view(["POST"])
@permission_classes([HasTokenPermission])
def getUserInfoById(request):
    user_id = request.data.get("id")

    if not user_id:
        return Response(
            {"message": "id is not provided"},
            status=status.HTTP_400_BAD_REQUEST
        )
    print("user id is ",user_id)

    try:
        user = Users.objects.get(id=user_id)
        serializer = UsersSerializer(user)
        return Response(
            {
                "user": serializer.data
            },
            status=status.HTTP_200_OK
        )

    except Users.DoesNotExist:
        return Response(
            {"message": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )





@api_view(["POST"])
@permission_classes([HasTokenPermission])
def deposit_to_treasury(request):
    """
    Handles deposit or withdrawal to/from the treasury.
    Expects: amount, description, type ('IN'/'OUT'), userId, channel
    """
    amount = request.data.get("amount")
    tx_type = request.data.get("type")
    user_id = request.data.get("userId")
    channel = request.data.get("channel")
    description= request.data.get("description", "")

    # Validate input
    if not user_id:
        return Response({"message": "userId not provided"}, status=status.HTTP_400_BAD_REQUEST)

    if amount is None:
        return Response({"message": "Amount not provided"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount = float(amount)
    except ValueError:
        return Response({"message": "Amount must be a number"}, status=status.HTTP_400_BAD_REQUEST)

    if tx_type not in ["IN", "OUT"]:
        return Response({"message": "type must be 'IN' or 'OUT'"}, status=status.HTTP_400_BAD_REQUEST)

    if channel not in ["cash", "bankily", "sedad", "bimBank", "masrivy", "click", "debt"]:
        return Response({"message": "Invalid channel"}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure user exists
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        with db_transaction.atomic():
            treasury = Treasury.objects.latest("last_update")

            # Map channel to the right treasury field
            channel_map = {
                "cash": "balance",
                "bankily": "Bankily_balance",
                "sedad": "Sedad_balance",
                "bimBank": "BimBank_balance",
                "masrivy": "Masrivy_balance",
                "click": "Click_balance",
            }

            # Handle debt case separately (could be unlimited or another model)
            if channel == "debt":
                # Example: just create a transaction without changing treasury
                message = f"قام {user.name} بإضافة دين بقيمة {amount}"
                trans = Transaction.objects.create(
                    type=tx_type,
                    amount=amount,
                    before=0,
                    after=0,
                    reason=message,
                    userName=user.name,
                    user=user,
                )
                return Response({"message": "Debt recorded successfully"}, status=status.HTTP_200_OK)

            # Get current balance for channel
            field_name = channel_map[channel]
            current_balance = getattr(treasury, field_name, 0)

            # Calculate new balance
            new_balance = current_balance + amount if tx_type == "IN" else current_balance - amount

            if new_balance < 0:
                return Response({"message": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

            # Transaction message
            action = "إيداع" if tx_type == "IN" else "سحب"
            message = f"قام {user.name} ب{action} {amount} عبر {channel}"
            if description:
                message = f" {description}"

            # Create transaction record
            trans = Transaction.objects.create(
                type=tx_type,
                amount=amount,
                before=current_balance,   # <-- رصيد القناة قبل العملية
                after=new_balance,        # <-- رصيد القناة بعد العملية
                channel=channel,          # <-- مهم عشان نعرف العملية كانت على أي قناة
                reason=message,
                userName=user.name,
                user=user,
            )
            # Create new treasury snapshot
            new_treasury = Treasury.objects.create(
                userName=user.name,
                user=user,
                balance=treasury.balance,
                Bankily_balance=treasury.Bankily_balance,
                Sedad_balance=treasury.Sedad_balance,
                BimBank_balance=treasury.BimBank_balance,
                Masrivy_balance=treasury.Masrivy_balance,
                Click_balance=treasury.Click_balance,
                transaction=trans,
            )

            # Update only the right field
            setattr(new_treasury, field_name, new_balance)
            new_treasury.save()
            serialize=TreasurySerializer(new_treasury)

        return Response(
            {
                "message": "Transaction completed successfully",
                "channel": channel,
                "newBalance": new_balance,
                "new_treasury":serialize.data
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response({"message": f"Error processing transaction: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(["POST"])
@permission_classes([HasTokenPermission])
def registerSales(request):
    sales_data = request.data.get("sales")
    type=request.data.get("type")
    print("request data ",request.data)

    if not sales_data:
        return Response(
            {"message": "sales_data is not provided"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(sales_data, list):
        return Response(
            {"message": "sales_data must be a list"},
            status=status.HTTP_400_BAD_REQUEST
        )

    errors = []
    created_sales = []

    for idx, sale in enumerate(sales_data, start=1):
        try:
            # Extract values safely
            name = sale.get("name")
            productId = int(sale.get("productId"))
            userId = int(sale.get("userId"))
            price = float(sale.get("price"))
            quantity = float(sale.get("quantity"))

            # Validate required fields
            if not all([name, price, quantity, productId, userId]):
                errors.append({"row": idx, "error": "Missing required fields"})
                continue

            # Fetch product & user
            try:
                product = Product.objects.get(id=productId)
            except ObjectDoesNotExist:
                errors.append({"row": idx, "error": f"Product {productId} not found"})
                continue

            try:
                user = Users.objects.get(id=userId)
            except ObjectDoesNotExist:
                errors.append({"row": idx, "error": f"User {userId} not found"})
                continue

            # Calculate benefit (all Decimal)
            benefit = 0
            if(product.purchase_price < price):
                benefit=(price - product.purchase_price) * quantity

            # Create sale
            sale_obj = Sales.objects.create(
                ProductName=name,
                userName=user.name,
                description="",
                price_unit=price,
                price_total=price * quantity,
                benefit=benefit,
                quantity=quantity,
                product=product,
                type=type,
                user=user
            )
            created_sales.append(sale_obj.id)
            product.stock_quantity=product.stock_quantity-quantity
            product.save()
            treasury=Treasury.objects.latest('last_update')
            total_balance=0
            if(type=='cash'):
                total_balance=treasury.balance
            if(type=='bankily'):
                total_balance=treasury.Bankily_balance
            if(type=='sedad'):
                total_balance=treasury.Sedad_balance
            if(type=='bimBank'):
                total_balance=treasury.BimBank_balance
            if(type=='masrivy'):
                total_balance=treasury.Masrivy_balance
            if(type=='click'):
                total_balance=treasury.Click_balance

            try:
                reason=f"تم بيع {quantity}  {product.name} عن طريق {type} بسعر {price}  للقطعة"
                trans=Transaction.objects.create(
                    type='IN',
                    amount=price * quantity,
                    before=total_balance,
                    after=total_balance+ (price * quantity),
                    reason = reason,
                    userName=user.name,
                    user=user,
                    sale=sale_obj,
                    channel=type
                )
                
                if trans:
                    # Copy old treasury values
                    new_treasury = Treasury.objects.create(
                        userName=user.name,
                        user=user,
                        balance=treasury.balance,
                        Bankily_balance=treasury.Bankily_balance,
                        Sedad_balance=treasury.Sedad_balance,
                        BimBank_balance=treasury.BimBank_balance,
                        Masrivy_balance=treasury.Masrivy_balance,
                        Click_balance=treasury.Click_balance,
                        transaction=trans
                    )

                    # Increase balance by type
                    if type == 'cash':
                        new_treasury.balance += (price * quantity)
                    elif type == 'bankily':
                        new_treasury.Bankily_balance += (price * quantity)
                    elif type == 'sedad':
                        new_treasury.Sedad_balance += (price * quantity)
                    elif type == 'bimBank':
                        new_treasury.BimBank_balance += (price * quantity)
                    elif type == 'masrivy':
                        new_treasury.Masrivy_balance += (price * quantity)
                    elif type == 'click':
                        new_treasury.Click_balance += (price * quantity)

                    new_treasury.save()
                    try:
                        # print("sending message ....")
                        sendTelgramMessage(reason)
                    except Exception as e:
                        print(e)
            except Exception as e:
                errors.append({"row": idx, "the transaction failed ": str(e)})

        except (InvalidOperation, ValueError) as e:
            errors.append({"row": idx, "error": str(e)})
        except Exception as e:
            errors.append({"row": idx, "error": f"Unexpected error: {str(e)}"})

    if errors:
        print("errors ",errors)
        return Response(
            {"message": "Some sales failed", "errors": errors, "created": created_sales},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {"message": "Sales registered successfully", "created": created_sales},
        status=status.HTTP_201_CREATED
    )


from django.shortcuts import get_object_or_404
from django.db import transaction
 

@api_view(["POST"])
@permission_classes([HasTokenPermission])
def CancelSale(request):
    sale_id = request.data.get("sale_id")
    user_id = request.data.get("user_id")
    print("request data ",request.data)


    if not sale_id or not user_id:
        return Response(
            {"message": "sale_id and user_id are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    sale = get_object_or_404(Sales, id=sale_id)
    user = get_object_or_404(Users, id=user_id)

    if sale.canceled:
        return Response(
            {"message": "This sale has already been canceled."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            # Mark sale as canceled
            sale.canceled = True
            sale.save()

            # Restore stock
            product = sale.product
            product.stock_quantity += sale.quantity
            product.save()

            reason = None
            trans = None

            # --- Case 1: Sale is on debt ---
            if sale.type == "debt":
                bill = sale.bill
                bill.balance -= sale.price_total
                bill.save()

                debt = Debts.objects.filter(bill=bill).first()
                if debt:
                    debt.balance -= sale.price_total
                    debt.initAmount-=sale.price_total
                    debt.description = f"فاتورة محدثة، الرصيد المتبقي {debt.balance}"
                    debt.save()

                reason = (
                    f"تم إلغاء بيع {sale.quantity} {product.name} "
                    f"بسعر {sale.price_unit} للقطعة عن طريق الدين"
                )

                trans = Transaction.objects.create(
                    type="OUT",
                    amount=sale.price_total,
                    before=debt.balance + sale.price_total if debt else 0,
                    after=debt.balance if debt else 0,
                    reason=reason,
                    userName=user.name,
                    user=user,
                    sale=sale,
                    channel="debt"
                )

            # --- Case 2: Sale is cash / bankily / etc. ---
            else:
                treasury = Treasury.objects.latest("last_update")
                balances = {
                    "cash": treasury.balance,
                    "bankily": treasury.Bankily_balance,
                    "sedad": treasury.Sedad_balance,
                    "bimBank": treasury.BimBank_balance,
                    "masrivy": treasury.Masrivy_balance,
                    "click": treasury.Click_balance,
                }

                if sale.type not in balances:
                    return Response(
                        {"message": f"Unknown sale type '{sale.type}'"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                before_balance = balances[sale.type]
                after_balance = before_balance - sale.price_total

                reason = (
                    f"تم إلغاء بيع {sale.quantity} {product.name} "
                    f"بسعر {sale.price_unit} للقطعة عن طريق {sale.type}"
                )

                trans = Transaction.objects.create(
                    type="OUT",
                    amount=sale.price_total,
                    before=before_balance,
                    after=after_balance,
                    reason=reason,
                    userName=user.name,
                    user=user,
                    sale=sale,
                    channel=sale.type,
                )

                # Clone treasury snapshot
                new_treasury = Treasury.objects.create(
                    userName=user.name,
                    user=user,
                    balance=treasury.balance,
                    Bankily_balance=treasury.Bankily_balance,
                    Sedad_balance=treasury.Sedad_balance,
                    BimBank_balance=treasury.BimBank_balance,
                    Masrivy_balance=treasury.Masrivy_balance,
                    Click_balance=treasury.Click_balance,
                    transaction=trans,
                )

                # Deduct dynamically
                field_map = {
                    "cash": "balance",
                    "bankily": "Bankily_balance",
                    "sedad": "Sedad_balance",
                    "bimBank": "BimBank_balance",
                    "masrivy": "Masrivy_balance",
                    "click": "Click_balance",
                }
                setattr(
                    new_treasury,
                    field_map[sale.type],
                    getattr(new_treasury, field_map[sale.type]) - sale.price_total,
                )
                new_treasury.save()

            # --- Send Telegram notification (optional) ---
            if reason:
                try:
                    sendTelgramMessage(reason)
                except Exception as e:
                    print("Telegram send failed:", e)

            return Response(
                {"message": "Sale canceled successfully", "sale_id": sale.id},
                status=status.HTTP_200_OK,
            )

    except Exception as e:
        return Response(
            {"message": "Error canceling sale", "error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )




@api_view(["POST"])
@permission_classes([HasTokenPermission])
def registerSales_debt(request):
    print("request data ",request.data)
    sales_data = request.data.get("sales")
    phone = request.data.get("phone")
    debt_id = request.data.get("debt_id")
    debt_avance = request.data.get("debt_avance", 0)
    debt_type = request.data.get("debt_type")  # "new" or "existing"
    debt_username = request.data.get("debt_username")
    total = float(request.data.get("total", 0))
    debt_payment_type=request.data.get("debt_payment_type")
    
    
    if debt_avance > total:
        # writ it in arabic
        return Response({"message": "المبلغ المدفوع لا يمكن أن يكون أكبر من المبلغ الإجمالي"}, status=status.HTTP_400_BAD_REQUEST)

    if not sales_data or not isinstance(sales_data, list):
        return Response({"message": "Invalid or missing sales_data"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    created_sales = []
    bill = None
    debt = None
    user = None

    # Handle debt creation or retrieval
    try:
        if debt_id:
            # Add to existing debt
            debt = Debts.objects.get(id=debt_id)
            bill = debt.bill or Bills.objects.create(phone=phone, balance=0)
        else:
            # Create new debt
            bill = Bills.objects.create(phone=phone, balance=0)
            debt = Debts.objects.create(
                name=debt_username,
                phone=phone,
                description=f"دين جديد بقيمة {total}",
                balance=0,
                initAmount=0,
                bill=bill
            )
    except Debts.DoesNotExist:
        return Response({"message": f"Debt with id {debt_id} not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("Error initializing debt:", e)
        return Response({"message": f"Error initializing debt: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # Process each sale
    for idx, sale in enumerate(sales_data, start=1):
        try:
            name = sale.get("name")
            productId = int(sale.get("productId"))
            userId = int(sale.get("userId"))
            price = float(sale.get("price"))
            quantity = float(sale.get("quantity"))
            

            if not all([name, productId, userId, price, quantity]):
                errors.append({"row": idx, "error": "Missing required fields"})
                continue

            product = Product.objects.filter(id=productId).first()
            if not product:
                errors.append({"row": idx, "error": f"Product {productId} not found"})
                continue

            user = Users.objects.filter(id=userId).first()
            if not user:
                errors.append({"row": idx, "error": f"User {userId} not found"})
                continue

            benefit = 0
            if product.purchase_price < price:
                benefit = (price - product.purchase_price) * quantity

            # Create Sale
            sale_obj = Sales.objects.create(
                ProductName=name,
                userName=user.name,
                description="",
                price_unit=price,
                price_total=price * quantity,
                benefit=benefit,
                quantity=quantity,
                product=product,
                bill=bill,
                type="debt",
                user=user
            )

            # Update product stock
            product.stock_quantity -= quantity
            product.save()

            created_sales.append(sale_obj.id)

        except Exception as e:
            print("Error processing sale row:", e)
            errors.append({"row": idx, "error": f"Unexpected error: {str(e)}"})

    # Update debt and bill totals
    try:
        bill.balance += total
        bill.save()

        debt.balance += total
        debt.initAmount += total
        debt.bill = bill
        debt.save()

        # Log the debt creation/addition
        DebtsPayment.objects.create(
            user=user,
            userName=user.name if user else "",
            debt=debt,
            balance=total,
            isDeposit=True
        )

        # Handle partial payment (avance)
        if debt_avance and int(debt_avance) > 0:
            avance_amount = int(debt_avance)
            debt.balance -= avance_amount
            debt.save()

            # Create payment record
            DebtsPayment.objects.create(
                user=user,
                userName=user.name if user else "",
                debt=debt,
                type=debt_payment_type,
                balance=avance_amount,
                isDeposit=False  # means payment (reducing debt)
            )

            # Record transaction
            treasury = Treasury.objects.latest('last_update')
            total_balance=0
            if(debt_payment_type=='cash'):
                total_balance=treasury.balance
            if(debt_payment_type=='bankily'):
                total_balance=treasury.Bankily_balance
            if(debt_payment_type=='sedad'):
                total_balance=treasury.Sedad_balance
            if(debt_payment_type=='bimBank'):
                total_balance=treasury.BimBank_balance
            if(debt_payment_type=='masrivy'):
                total_balance=treasury.Masrivy_balance
            if(debt_payment_type=='click'):
                total_balance=treasury.Click_balance
            
            if treasury:


                trans=Transaction.objects.create(
                    type="IN",
                    amount=avance_amount,
                    before=total_balance,
                    after=total_balance + avance_amount,
                    reason=f"دفع جزء من الدين بقيمة {avance_amount} من {debt.name}",
                    user=user,
                    userName=user.name,
                    channel=debt_payment_type
                )
                if trans:
                    new_treasury = Treasury.objects.create(
                    userName=user.name,
                    user=user,
                    balance=treasury.balance,
                    Bankily_balance=treasury.Bankily_balance,
                    Sedad_balance=treasury.Sedad_balance,
                    BimBank_balance=treasury.BimBank_balance,
                    Masrivy_balance=treasury.Masrivy_balance,
                    Click_balance=treasury.Click_balance,
                    transaction=trans
                )
                    
                                            # Increase balance by type
                    if debt_payment_type == 'cash':
                        new_treasury.balance += avance_amount
                    elif debt_payment_type == 'bankily':
                        new_treasury.Bankily_balance += avance_amount
                    elif debt_payment_type == 'sedad':
                        new_treasury.Sedad_balance += avance_amount
                    elif debt_payment_type == 'bimBank':
                        new_treasury.BimBank_balance += avance_amount
                    elif debt_payment_type == 'masrivy':
                        new_treasury.Masrivy_balance += avance_amount
                    elif debt_payment_type == 'click':
                        new_treasury.Click_balance += avance_amount

                    new_treasury.save()

        # Telegram notification
        msg = f"تم {'إضافة' if debt_id else 'إنشاء'} دين بقيمة {total} إلى {debt_username} رقم الهاتف {phone}"
        if debt_avance and int(debt_avance) > 0:
            msg += f" مع تسديد مبلغ {debt_avance}."
        sendTelgramMessage(msg)
        print("status ",200)

        return Response({
            "message": "Debt processed successfully",
            "debt_id": debt.id,
            "created_sales": created_sales,
            "errors": errors if errors else None
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("Error saving debt:", e)
        return Response({"message": f"Error saving debt: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)






@api_view(["POST"])
@permission_classes([HasTokenPermission])
def add_products(request):
    print("request data ",request.data)

    products = request.data.get("products")
    supplier_id = request.data.get("supplier")

    if not products:
        return Response(
            {"message": "products is not provided"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(products, list):
        return Response(
            {"message": "products must be a list"},
            status=status.HTTP_400_BAD_REQUEST
        )

    errors = []
    created_products = []
    bill = []
    totale = 0

    supplier = None
    if supplier_id and supplier_id != 0:
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return Response(
                {"message": f"Supplier with id {supplier_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    for idx, sale in enumerate(products, start=1):
        try:
            # Extract values safely
            name = sale.get("name")
            purchase_price = int(sale.get("purchase_price"))
            sale_price = int(sale.get("sale_price"))
            stock_quantity = float(sale.get("stock_quantity"))

            # Create product with supplier if available
            product = Product.objects.create(
                name=name,
                purchase_price=purchase_price,
                sale_price=sale_price,
                stock_quantity=stock_quantity,
                supplier=supplier  # <-- Add supplier FK
            )
            created_products.append(product.id)

            if product:
                message = f"{stock_quantity} من {name} بسعر {purchase_price} للقطعة"
                bill.append(message)
                totale += (purchase_price * stock_quantity)

        except (InvalidOperation, ValueError) as e:
            errors.append({"row": idx, "error": str(e)})
        except Exception as e:
            errors.append({"row": idx, "error": f"Unexpected error: {str(e)}"})

    # Only create debt if supplier exists
    if supplier:
        try:
            SuppliersDebts.objects.create(
                name=supplier.name,
                phone=supplier.phone,
                balance=totale,
                initAmount=totale,
                bill=bill,
                supplier=supplier
            )
            # sendTelgramMessage(f"تمت إضافة دين بقيمة {totale} إلى {supplier.name} رقم الهاتف {supplier.phone}")
        except Exception as e:
            print("Error creating debt:", e)

    if errors:
        print("errors ",errors)
        return Response(
            {"message": "Some products failed", "errors": errors, "created": created_products},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    print("status 201")
    return Response(
        {"message": "Products registered successfully", "created": created_products},
        status=status.HTTP_201_CREATED
    )



def generate_random_string(length=30):
    # Characters to choose from: letters (upper + lower) + digits
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

 
def addNewUser(name , email , password , roles):
    user = Users.objects.create(
    name=name,
    email=email,
    password="1234",
    token=generate_random_string(),
    roles=roles
    )
    
    # if user:
    #     send_email(email, "test")

class UserViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer
    permission_classes = [HasTokenPermission]
    def update(self, request, *args, **kwargs):
        # Get the user instance
        user = self.get_object()  # fetches the instance based on URL pk

        # Deserialize the request data
        if  request.data['password'] == "":
            request.data['password']=user.password
        else :
            request.data['password']=hash(request.data['password'])
            
            
        serializer = UsersSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()  # update in DB
            return Response(
                {
                    "message": "تم تحديث المستخدم بنجاح",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "message": "بيانات غير صالحة",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
        
    def create(self, request, *args, **kwargs):
        data = request.data.copy()  # make a mutable copy

        email = data.get('email')
        phone = data.get('phone')

        # Check if email already exists
        if Users.objects.filter(email=email).exists():
            return Response(
                {"message": "البريد الإلكتروني موجود بالفعل"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if phone already exists
        if Users.objects.filter(phone=phone).exists():
            return Response(
                {"message": "رقم الهاتف موجود بالفعل"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Hash the password before saving
        if 'password' in data:
            data['password'] = hash(data['password'])

        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            user = serializer.save(token=generate_random_string())
            return Response(
                {
                    "message": "تم إنشاء المستخدم بنجاح",
                    "data": UsersSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {
                    "message": "بيانات غير صحيحة",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    def get_queryset(self):
        return Supplier.objects.all().order_by('-created_at')
    permission_classes = [HasTokenPermission]
    
    

class EmployeeTransactionViewSet(viewsets.ModelViewSet):
    queryset = EmployeeTransaction.objects.all()
    serializer_class = EmployeeTransactionSerializer
    def get_queryset(self):
        return EmployeeTransaction.objects.all().order_by('-created_at')

    permission_classes = [HasTokenPermission]
    
@api_view(["POST"])
@permission_classes([HasTokenPermission])
def get_employee_transactions(request):
    emp_id = request.data.get("emp_id")
    if not emp_id:
        return Response({"error": "emp_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Safer than .get() because it returns 404 automatically
    employee = get_object_or_404(Employee, id=emp_id)

    transactions = EmployeeTransaction.objects.filter(employee=employee).order_by("-created_at")

    employee_data = EmployeeSerializer(employee).data
    transactions_data = EmployeeTransactionSerializer(transactions, many=True).data

    return Response({
        "employee": employee_data,
        "transactions": transactions_data
    }, status=status.HTTP_200_OK)
    

class ProductTrackUpdateViewSet(viewsets.ModelViewSet):
    queryset = ProductTrackUpdate.objects.all().order_by('-updated_at')
    serializer_class = ProductTrackUpdateSerializer
    permission_classes = [HasTokenPermission]

    # Optional: Filter by product or user
    def get_queryset(self):
        queryset = ProductTrackUpdate.objects.all().order_by('-updated_at')
        product_id = self.request.query_params.get('product_id')
        user_id = self.request.query_params.get('user_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if user_id:
            queryset = queryset.filter(updated_by_id=user_id)
        return queryset
    


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [HasTokenPermission]

    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')

    def perform_update(self, serializer):
        # Get user ID from the request data
        user_id = self.request.data.get("user_id")  

        # Get the old product before update
        instance = self.get_object()
        old_data = {
            'name': instance.name,
            'description': instance.description,
            'purchase_price': instance.purchase_price,
            'sale_price': instance.sale_price,
            'stock_quantity': instance.stock_quantity,
        }

        # Save the updated product
        updated_instance = serializer.save()
        user=Users.objects.get(id=user_id)

        # Track changes
        tracked_fields = ['name', 'description', 'purchase_price', 'sale_price', 'stock_quantity']
        for field in tracked_fields:
            old_value = old_data[field]
            new_value = getattr(updated_instance, field)
            if old_value != new_value:
                ProductTrackUpdate.objects.create(
                    product=updated_instance,
                    field_name=field,
                    old_value=old_value,
                    productName=updated_instance.name,
                    new_value=new_value,
                    userName=user.name,
                    updated_by_id=user_id  # ✅ use _id to assign directly
                )



class SalesViewSet(viewsets.ModelViewSet):

    queryset = Sales.objects.all()
    serializer_class = SalesSerializer
    permission_classes = [HasTokenPermission]
    def get_queryset(self):
        return Sales.objects.all().order_by('-created_at')
    
class TransactionViewSet(viewsets.ModelViewSet):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [HasTokenPermission]
    def get_queryset(self):
        return Transaction.objects.all().order_by('-created_at')
class TreasuryViewSet(viewsets.ModelViewSet):

    queryset = Treasury.objects.all()
    serializer_class = TreasurySerializer
    permission_classes = [HasTokenPermission]

         
                

class SuppliersDebtsViewSet(viewsets.ModelViewSet):

    queryset = SuppliersDebts.objects.all()
    serializer_class = SuppliersDebtsSerializer
    def get_queryset(self):
        return SuppliersDebts.objects.all().order_by('-created_at')
    permission_classes = [HasTokenPermission]

 
                
               
class EmployeeViewSet(viewsets.ModelViewSet):

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    def get_queryset(self):
        return Employee.objects.all().order_by('-created_at')
    permission_classes = [HasTokenPermission]


 



class DepositsViewSet(viewsets.ModelViewSet):

    queryset = Deposits.objects.all()
    serializer_class = DepositsSerializer
    permission_classes = [HasTokenPermission]
    def get_queryset(self):
        return Deposits.objects.all().order_by('-created_at')




class DebtsViewSet(viewsets.ModelViewSet):

    queryset = Debts.objects.all()
    serializer_class = DebtsSerializer
    permission_classes = [HasTokenPermission]
    def get_queryset(self):
        return Debts.objects.all().order_by('-created_at')
class BillsViewSet(viewsets.ModelViewSet):
    queryset = Bills.objects.all()
    serializer_class = BillsSerializer
    permission_classes = [HasTokenPermission]
    
    


class DepositsPaymentViewSet(viewsets.ModelViewSet):
    queryset = DepositsPayment.objects.all()
    serializer_class = DepositsPaymentSerializer
    permission_classes = [HasTokenPermission]

 
    def perform_create(self, serializer):
        # Save the payment first
        payment = serializer.save()
        type=payment.type

        # Update the related debt balance
        if payment.Deposits:
            debt = payment.Deposits
            newBalance=0
            if payment.isDeposit:
                newBalance=debt.balance + payment.balance
            else:
                newBalance=debt.balance - payment.balance
            deposit = payment.Deposits
            deposit.balance = max(0, newBalance)  # prevent negative balance
            # If balance is zero, mark as done
            if deposit.balance == 0:
                deposit.done = True
            deposit.save()
            if deposit:
                
                
                treasury=Treasury.objects.latest('last_update')
                total_balance=0
                
                if(type=='cash'):
                    total_balance=treasury.balance
                if(type=='bankily'):
                    total_balance=treasury.Bankily_balance
                if(type=='sedad'):
                    total_balance=treasury.Sedad_balance
                if(type=='bimBank'):
                    total_balance=treasury.BimBank_balance
                if(type=='masrivy'):
                    total_balance=treasury.Masrivy_balance
                if(type=='click'):
                    total_balance=treasury.Click_balance
                
                try:
                    reason=f"تم تسديد {payment.balance} من وديعة {debt.name} عن طريق {type}"
                    trans_type='OUT'
                    after=total_balance + payment.balance
                    reason=f"تم سحب {payment.balance} من وديعة {deposit.name} عن طريق {type}"
                    if payment.isDeposit:
                        trans_type='IN'
                        after=total_balance - payment.balance
                        reason=f"تم إيداع {payment.balance} إلى وديعة {debt.name} عن طريق {type}"
                    trans=Transaction.objects.create(
                        type=trans_type,
                        amount=payment.balance,
                        before=total_balance,
                        after=after,
                        reason = reason,
                        userName=payment.user.name,
                        user=payment.user,
                        channel=type
                    )
                    
                    if trans:
                        # Copy old treasury values
                        new_treasury = Treasury.objects.create(
                            userName=payment.user.name,
                            user=payment.user,
                            balance=treasury.balance,
                            Bankily_balance=treasury.Bankily_balance,
                            Sedad_balance=treasury.Sedad_balance,
                            BimBank_balance=treasury.BimBank_balance,
                            Masrivy_balance=treasury.Masrivy_balance,
                            Click_balance=treasury.Click_balance,
                            transaction=trans
                        )

                        # Increase balance by type
                        if type == 'cash':
                            if payment.isDeposit:
                                new_treasury.balance += payment.balance
                            else:
                                new_treasury.balance -= payment.balance
                        elif type == 'bankily':
                            if payment.isDeposit:
                                new_treasury.Bankily_balance += payment.balance
                            else:
                                new_treasury.Bankily_balance -= payment.balance
                        elif type == 'sedad':
                            if payment.isDeposit:
                                new_treasury.Sedad_balance += payment.balance
                            else:
                                new_treasury.Sedad_balance -= payment.balance
                        elif type == 'bimBank':
                            if payment.isDeposit:
                                new_treasury.BimBank_balance += payment.balance
                            else:
                                new_treasury.BimBank_balance -= payment.balance
                        elif type == 'masrivy':
                            if payment.isDeposit:
                                new_treasury.Masrivy_balance += payment.balance
                            else:
                                new_treasury.Masrivy_balance -= payment.balance
                        elif type == 'click':
                            if payment.isDeposit:
                                new_treasury.Click_balance += payment.balance
                            else:
                                new_treasury.Click_balance -= payment.balance

                        new_treasury.save()
                        try:
                            # print("sending message ....")
                            sendTelgramMessage(reason)
                        except Exception as e:
                            print(e)
                except Exception as e:
                    print(e)
                # msg=f"تم تسديد {payment.balance} من أصل {deposit.initAmount} من وديعة {deposit.name} عن طريق {payment.type} و الباقي {deposit.balance}"
                # sendTelgramMessage(msg)




from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Employee, EmployeeTransaction, Transaction, Treasury, Users
from .permissions import HasTokenPermission


@api_view(["POST"])
@permission_classes([HasTokenPermission])
def addEmployeeTrans(request):
    """
    Handles employee transactions (debt, deposit, salary, adjustment)
    and updates both employee debt balance and treasury balances.
    """

    emp_id = int(request.data.get("emp_id"))
    user_id = int(request.data.get("user_id"))
    amount = int(request.data.get("amount"))
    trans_type = request.data.get("trans_type")   # debt | deposit | salary | adjustment
    channel = request.data.get("channel", "cash")  # default = cash
    note = request.data.get("note", "")

    # Validate required fields
    if not emp_id or not user_id or not amount or not trans_type:
        
        return Response(
            {"message": "employee_id, user_id, amount and type are required",'data':request.data},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get employee & user
    employee = get_object_or_404(Employee, id=emp_id)
    user = get_object_or_404(Users, id=user_id)

    # Get latest treasury snapshot
    treasury = Treasury.objects.latest("last_update")

    # Detect which balance field to update
    channel_field_map = {
        "cash": "balance",
        "bankily": "Bankily_balance",
        "sedad": "Sedad_balance",
        "bimbank": "BimBank_balance",
        "masrivy": "Masrivy_balance",
        "click": "Click_balance",
    }

    balance_field = channel_field_map.get(channel.lower())
    if not balance_field:
        return Response(
            {"message": f"Invalid channel '{channel}'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Current balance before transaction
    before_balance = getattr(treasury, balance_field)
    after_balance = before_balance

    # Transaction logic
    reason = ""
    transaction_type = Transaction.CASH_IN  # default

    if trans_type == "debt":
        # Employee takes debt → treasury gives OUT
        after_balance = before_balance - int(amount)
        reason = f"إعطاء دين بقيمة {amount} للموظف {employee.name} عن طريق {channel}"
        transaction_type = Transaction.CASH_OUT

    elif trans_type == "deposit":
        # Employee pays back debt → treasury gets IN
        after_balance = before_balance + int(amount)
        reason = f"تسديد {amount} من دين الموظف {employee.name} عن طريق {channel}"
        transaction_type = Transaction.CASH_IN

    elif trans_type == "salary":
        # Employee takes salary → treasury OUT
        after_balance = before_balance - int(amount)
        reason = f"صرف راتب {amount} للموظف {employee.name} عن طريق {channel}"
        transaction_type = Transaction.CASH_OUT

    elif trans_type == "adjustment":
        # Manual debt adjustment (doesn't affect treasury directly)
        reason = f"تعديل يدوي بقيمة {amount} لحساب الموظف {employee.name}"
        transaction_type = Transaction.CASH_OUT

    else:
        return Response({"message": "Invalid transaction type"}, status=status.HTTP_400_BAD_REQUEST)

    # Create EmployeeTransaction (updates employee debt automatically via model save)
    emp_trans = EmployeeTransaction.objects.create(
        employee=employee,
        type=trans_type,
        amount=amount,
        note=note or reason,
        channel=channel,
    )

    # Create financial Transaction record
    trans = Transaction.objects.create(
        type=transaction_type,
        amount=amount,
        before=before_balance,
        after=after_balance,
        reason=reason,
        user=user,
        userName=user.name,
        channel=channel
    )

    # Create new treasury snapshot with updated balances
    new_treasury = Treasury.objects.create(
        userName=user.name,
        user=user,
        balance=treasury.balance,
        Bankily_balance=treasury.Bankily_balance,
        Sedad_balance=treasury.Sedad_balance,
        BimBank_balance=treasury.BimBank_balance,
        Masrivy_balance=treasury.Masrivy_balance,
        Click_balance=treasury.Click_balance,
        transaction=trans
    )

    # Apply balance update to the correct channel
    if trans_type in ["debt", "deposit", "salary"]:
        setattr(new_treasury, balance_field, after_balance)
        new_treasury.save()

    return Response({
        "message": "Transaction recorded successfully",
        "employee": {
            "id": employee.id,
            "name": employee.name,
            "debt_balance": employee.debt_balance
        },
        "transaction": {
            "id": emp_trans.id,
            "type": emp_trans.type,
            "amount": emp_trans.amount,
            "note": emp_trans.note,
            "channel": emp_trans.channel,
            "created_at": emp_trans.created_at
        },
        "treasury": {
            "before": before_balance,
            "after": after_balance,
            "channel": channel
        }
    }, status=status.HTTP_201_CREATED)
      
    
    
class SuppliersDebtsPaymentViewSet(viewsets.ModelViewSet):

    queryset = SuppliersDebtsPayment.objects.all()
    serializer_class = SuppliersDebtsPaymentSerializer
    permission_classes = [HasTokenPermission]
    def perform_create(self, serializer):
        # Save the payment first
        payment = serializer.save()
        type=payment.type

  
        # Update the related debt balance
        if payment.debt:
            debt = payment.debt
            newBalance=0
            if payment.isDeposit:
                newBalance=debt.balance + payment.balance
            else:
                newBalance=debt.balance - payment.balance
            debt.balance = max(0, newBalance)  # prevent negative balance
            # If balance is zero, mark as done
            if debt.balance == 0:
                debt.done = True
            debt.save()
            if debt:
                
                
                treasury=Treasury.objects.latest('last_update')
                total_balance=0
                
                if(type=='cash'):
                    total_balance=treasury.balance
                if(type=='bankily'):
                    total_balance=treasury.Bankily_balance
                if(type=='sedad'):
                    total_balance=treasury.Sedad_balance
                if(type=='bimBank'):
                    total_balance=treasury.BimBank_balance
                if(type=='masrivy'):
                    total_balance=treasury.Masrivy_balance
                if(type=='click'):
                    total_balance=treasury.Click_balance
                
                try:
                    reason=f"تم تسديد {payment.balance} من دين {debt.name} عن طريق {type}"
                    trans_type='IN'
                    after=total_balance + payment.balance
                    if payment.isDeposit:
                        trans_type='OUT'
                        after=total_balance - payment.balance
                        reason=f"تم إيداع {payment.balance} إلى دين {debt.name} عن طريق {type}"
                    trans=Transaction.objects.create(
                        type=trans_type,
                        amount=payment.balance,
                        before=total_balance,
                        after=after,
                        reason = reason,
                        userName=payment.user.name,
                        user=payment.user,
                        channel=type
                    )
                    
                    if trans:
                        # Copy old treasury values
                        new_treasury = Treasury.objects.create(
                            userName=payment.user.name,
                            user=payment.user,
                            balance=treasury.balance,
                            Bankily_balance=treasury.Bankily_balance,
                            Sedad_balance=treasury.Sedad_balance,
                            BimBank_balance=treasury.BimBank_balance,
                            Masrivy_balance=treasury.Masrivy_balance,
                            Click_balance=treasury.Click_balance,
                            transaction=trans
                        )

                        # Increase balance by type
                        if type == 'cash':
                            new_treasury.balance += payment.balance
                        elif type == 'bankily':
                            new_treasury.Bankily_balance += payment.balance
                        elif type == 'sedad':
                            new_treasury.Sedad_balance += payment.balance
                        elif type == 'bimBank':
                            new_treasury.BimBank_balance += payment.balance
                        elif type == 'masrivy':
                            new_treasury.Masrivy_balance += payment.balance
                        elif type == 'click':
                            new_treasury.Click_balance += payment.balance

                        new_treasury.save()
                        try:
                            # print("sending message ....")
                            sendTelgramMessage(reason)
                        except Exception as e:
                            print(e)
                except Exception as e:
                    print(e)

                # msg=f"تم تسديد {payment.balance} من أصل {debt.initAmount} من دين {debt.name} عن طريق {payment.type} و الباقي {debt.balance}"
                # sendTelgramMessage(msg)
                
       

class DebtsPaymentViewSet(viewsets.ModelViewSet):

    queryset = DebtsPayment.objects.all()
    serializer_class = DebtsPaymentSerializer
    permission_classes = [HasTokenPermission]
    def get_queryset(self):
        return DebtsPayment.objects.all().order_by('-created_at')
    def perform_create(self, serializer):
        # Save the payment first
        payment = serializer.save()
        type=payment.type

        # Update the related debt balance
        if payment.debt:
            debt = payment.debt
            newBalance=0
            if payment.isDeposit:
                newBalance=debt.balance + payment.balance
            else:
                newBalance=debt.balance - payment.balance
            debt.balance = max(0, newBalance)  # prevent negative balance
            # If balance is zero, mark as done
            if debt.balance == 0:
                debt.done = True
            debt.save()
            if debt:
                
                
                treasury=Treasury.objects.latest('last_update')
                total_balance=0
                
                if(type=='cash'):
                    total_balance=treasury.balance
                if(type=='bankily'):
                    total_balance=treasury.Bankily_balance
                if(type=='sedad'):
                    total_balance=treasury.Sedad_balance
                if(type=='bimBank'):
                    total_balance=treasury.BimBank_balance
                if(type=='masrivy'):
                    total_balance=treasury.Masrivy_balance
                if(type=='click'):
                    total_balance=treasury.Click_balance
                
                try:
                    reason=f"تم تسديد {payment.balance} من دين {debt.name} عن طريق {type}"
                    trans_type='IN'
                    after=total_balance + payment.balance
                    if payment.isDeposit:
                        trans_type='OUT'
                        after=total_balance - payment.balance
                        reason=f"تم إيداع {payment.balance} إلى دين {debt.name} عن طريق {type}"
                    trans=Transaction.objects.create(
                        type=trans_type,
                        amount=payment.balance,
                        before=total_balance,
                        after=after,
                        reason = reason,
                        userName=payment.user.name,
                        user=payment.user,
                        channel=type
                    )
                    
                    if trans:
                        # Copy old treasury values
                        new_treasury = Treasury.objects.create(
                            userName=payment.user.name,
                            user=payment.user,
                            balance=treasury.balance,
                            Bankily_balance=treasury.Bankily_balance,
                            Sedad_balance=treasury.Sedad_balance,
                            BimBank_balance=treasury.BimBank_balance,
                            Masrivy_balance=treasury.Masrivy_balance,
                            Click_balance=treasury.Click_balance,
                            transaction=trans
                        )

                        # Increase balance by type
                        if type == 'cash':
                            new_treasury.balance += payment.balance
                        elif type == 'bankily':
                            new_treasury.Bankily_balance += payment.balance
                        elif type == 'sedad':
                            new_treasury.Sedad_balance += payment.balance
                        elif type == 'bimBank':
                            new_treasury.BimBank_balance += payment.balance
                        elif type == 'masrivy':
                            new_treasury.Masrivy_balance += payment.balance
                        elif type == 'click':
                            new_treasury.Click_balance += payment.balance

                        new_treasury.save()
                        try:
                            # print("sending message ....")
                            sendTelgramMessage(reason)
                        except Exception as e:
                            print(e)
                except Exception as e:
                    print(e)

                # msg=f"تم تسديد {payment.balance} من أصل {debt.initAmount} من دين {debt.name} عن طريق {payment.type} و الباقي {debt.balance}"
                # sendTelgramMessage(msg)

        
        
        
@api_view(["GET"])
def get_total_debts_balance(request):
    total_balance = Debts.objects.aggregate(total=Sum("balance"))["total"] or 0
    return Response(
        {"total_balance": total_balance},
        status=status.HTTP_200_OK
    )
@api_view(["GET"])
def get_total_deposits_balance(request):
    total_balance = Deposits.objects.aggregate(total=Sum("balance"))["total"] or 0
    return Response(
        {"total_balance": total_balance},
        status=status.HTTP_200_OK
    )
@api_view(["GET"])

def get_total_supplires_balance_balance(request):
    total_balance = SuppliersDebts.objects.aggregate(total=Sum("balance"))["total"] or 0
    return Response(
        {"total_balance": total_balance},
        status=status.HTTP_200_OK
    )