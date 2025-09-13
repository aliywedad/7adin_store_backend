import random
import string
from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from store.permissions import HasTokenPermission
from .models import Supplier, Product, Users
from .serializers import *
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import check_password
import hashlib

def hash(password: str) -> str:

    md5_hash = hashlib.md5()
    md5_hash.update(password.encode('utf-8'))
    return md5_hash.hexdigest()


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
                "rolesGroupe": user.roles
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
def getUserInfoById(request):
    user_id = request.data.get("id")

    if not user_id:
        return Response(
            {"message": "id is not provided"},
            status=status.HTTP_400_BAD_REQUEST
        )

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

     








def send_email(recipient, body):
    source_email = "s3c.404@gmail.com"  # Your Gmail address
    password = 'wsaw jdjj yrsw pfqv'    # Your Gmail app password or regular password
    smtp_server = "smtp.gmail.com"      # Gmail SMTP server
    smtp_port = 587                     # Gmail SMTP port (TLS)

    subject = "Le mot de passe de l'application de l'examen pratique "

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = source_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Start TLS encryption
            server.starttls()

            # Log in to the SMTP server
            server.login(source_email, password)

            # Send the email
            server.sendmail(source_email, recipient, msg.as_string())

        print(f"Email sent successfully to {recipient}!")

    except Exception as e:
        print(f"Error: {e}")
        
        

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
    permission_classes = [HasTokenPermission]

class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [HasTokenPermission]
    
class SalesViewSet(viewsets.ModelViewSet):

    queryset = Sales.objects.all()
    serializer_class = SalesSerializer
    permission_classes = [HasTokenPermission]
    
    
class TransactionViewSet(viewsets.ModelViewSet):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [HasTokenPermission]
    
class TreasuryViewSet(viewsets.ModelViewSet):

    queryset = Treasury.objects.all()
    serializer_class = TreasurySerializer
    permission_classes = [HasTokenPermission]