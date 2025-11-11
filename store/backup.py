import json
import os
import smtplib
import traceback
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *

TOKEN = "8354361276:AAGjtf80Yvq4ftlO-dgNyOAHiYelW3ZzsbI"
CHAT_ID = "908603997"  # aliy
# CHAT_ID = "8064161003"  #med 

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
# https://api.telegram.org/bot8354361276:AAGjtf80Yvq4ftlO-dgNyOAHiYelW3ZzsbI/getUpdates


def sendTelgramMessage(msg):
    params = {"chat_id": CHAT_ID, "text": msg}

    # response = requests.get(url, params=params)

def send_email(recipient, body, file_path=None):
    source_email = "store.rossoapp@gmail.com"
    password = "qpns jgcx jkvx ebwq"  # Gmail App Password
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    subject = "Backup JSON file attached"

    msg = MIMEMultipart()
    msg['From'] = source_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(file_path)}",
        )
        msg.attach(part)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(source_email, password)
        server.sendmail(source_email, recipient, msg.as_string())


def send_to_telegram(file_path, message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"

    with open(file_path, "rb") as f:
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": message},
            files={"document": f}
        )

    if response.status_code != 200:
        raise Exception(f"Telegram API error: {response.json()}")


from django.core.serializers import serialize





def loadBackup():
    try:
        # serialize all data
        data = {
            "users": UsersSerializer(Users.objects.all(), many=True).data,
            "employees": json.loads(serialize("json", Employee.objects.all())),
            "EmployeeTransaction": json.loads(serialize("json", EmployeeTransaction.objects.all())),
            "suppliers": json.loads(serialize("json", Supplier.objects.all())),
            "products": ProductSerializer(Product.objects.all(), many=True).data,
            "bills": json.loads(serialize("json", Bills.objects.all())),
            "sales": json.loads(serialize("json", Sales.objects.all())),
            "transactions": TransactionSerializer(Transaction.objects.all(), many=True).data,
            "treasury": TreasurySerializer(Treasury.objects.all(), many=True).data,
            "debts": json.loads(serialize("json", Debts.objects.all())),
            "suppliersDebts": json.loads(serialize("json", SuppliersDebts.objects.all())),
            "suppliersDebtsPayment": json.loads(serialize("json", SuppliersDebtsPayment.objects.all())),
            "debtsPayment": json.loads(serialize("json", DebtsPayment.objects.all())),
            "deposits": json.loads(serialize("json", Deposits.objects.all())),
            "depositsPayment": json.loads(serialize("json", DepositsPayment.objects.all())),
            "backups": json.loads(serialize("json", Backup.objects.all())),
        }

        # الوقت والتاريخ
        now = datetime.now()
        formatted_date = now.strftime("%d %B %Y، %H:%M")

        # حفظ الملف
        json_file_path = "backup.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # الحجم
        file_size = os.path.getsize(json_file_path) / 1024  # KB
        size_str = f"{file_size:.2f} KB"
        message = f"📦 نسخة احتياطية بتاريخ {formatted_date}\n📂 حجم الملف: {size_str}"

        # إرسال النسخة
        send_to_telegram(json_file_path, message)
        send_email(
            recipient="22086@supnum.mr",
            body=message,
            file_path=json_file_path
        )

        # حفظ الحجم في قاعدة البيانات
        Backup.objects.create(size=size_str)

        # ✅ حذف الملف بعد الإرسال بنجاح
        if os.path.exists(json_file_path):
            os.remove(json_file_path)

        return {
            "message": message,
            "file_size_kb": round(file_size, 2),
            "date": formatted_date
        }

    except Exception as e:
        traceback.print_exc()
        raise Exception(f"Backup process failed: {e}")









@api_view(['GET'])
def send_backup(request):
    try:
        result = loadBackup()
        return Response(
            {
                "detail": "✅ Backup created and sent successfully.",
           
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        error_message = str(e)
        traceback.print_exc()
        return Response(
            {
                "detail": "❌ Backup failed.",
                "error": error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
