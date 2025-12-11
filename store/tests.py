
# class DebtsPaymentViewSet(viewsets.ModelViewSet):

#     queryset = DebtsPayment.objects.all()
#     serializer_class = DebtsPaymentSerializer
#     permission_classes = [HasTokenPermission]
#     def get_queryset(self):
#         return DebtsPayment.objects.all().order_by('-created_at')
#     def perform_create(self, serializer):
#         # Save the payment first
#         payment = serializer.save()
#         type=payment.type

#         # Update the related debt balance
#         if payment.debt:
#             debt = payment.debt
#             newBalance=0
#             if payment.isDeposit:
#                 newBalance=debt.balance + payment.balance
#             else:
#                 newBalance=debt.balance - payment.balance
#             debt.balance = max(0, newBalance)  # prevent negative balance
#             # If balance is zero, mark as done
#             if debt.balance == 0:
#                 debt.done = True
#             debt.save()
#             if debt:
                
                
#                 treasury=Treasury.objects.latest('last_update')
#                 total_balance=0
                
#                 if(type=='cash'):
#                     total_balance=treasury.balance
#                 if(type=='bankily'):
#                     total_balance=treasury.Bankily_balance
#                 if(type=='sedad'):
#                     total_balance=treasury.Sedad_balance
#                 if(type=='bimBank'):
#                     total_balance=treasury.BimBank_balance
#                 if(type=='masrivy'):
#                     total_balance=treasury.Masrivy_balance
#                 if(type=='click'):
#                     total_balance=treasury.Click_balance
                
#                 try:
#                     reason=f"تم تسديد {payment.balance} من دين {debt.name} عن طريق {type}"
#                     trans_type='IN'
#                     after=total_balance + payment.balance
#                     if payment.isDeposit:
#                         trans_type='OUT'
#                         after=total_balance - payment.balance
#                         reason=f"تم إيداع {payment.balance} إلى دين {debt.name} عن طريق {type}"
#                     trans=Transaction.objects.create(
#                         type=trans_type,
#                         amount=payment.balance,
#                         before=total_balance,
#                         after=after,
#                         reason = reason,
#                         userName=payment.user.name,
#                         user=payment.user,
#                         channel=type
#                     )
                    
#                     if trans:
#                         # Copy old treasury values
#                         new_treasury = Treasury.objects.create(
#                             userName=payment.user.name,
#                             user=payment.user,
#                             balance=treasury.balance,
#                             Bankily_balance=treasury.Bankily_balance,
#                             Sedad_balance=treasury.Sedad_balance,
#                             BimBank_balance=treasury.BimBank_balance,
#                             Masrivy_balance=treasury.Masrivy_balance,
#                             Click_balance=treasury.Click_balance,
#                             transaction=trans
#                         )

#                         # Increase balance by type
#                         # Update treasury depending on deposit or payment
#                         if type == 'cash':
#                             new_treasury.balance += -payment.balance if payment.isDeposit else payment.balance

#                         elif type == 'bankily':
#                             new_treasury.Bankily_balance += -payment.balance if payment.isDeposit else payment.balance

#                         elif type == 'sedad':
#                             new_treasury.Sedad_balance += -payment.balance if payment.isDeposit else payment.balance

#                         elif type == 'bimBank':
#                             new_treasury.BimBank_balance += -payment.balance if payment.isDeposit else payment.balance

#                         elif type == 'masrivy':
#                             new_treasury.Masrivy_balance += -payment.balance if payment.isDeposit else payment.balance

#                         elif type == 'click':
#                             new_treasury.Click_balance += -payment.balance if payment.isDeposit else payment.balance

#                         new_treasury.save()
#                         try:
#                             # print("sending message ....")
#                             sendTelgramMessage(reason)
#                         except Exception as e:
#                             print(e)
#                 except Exception as e:
#                     print(e)

#                 # msg=f"تم تسديد {payment.balance} من أصل {debt.initAmount} من دين {debt.name} عن طريق {payment.type} و الباقي {debt.balance}"
#                 # sendTelgramMessage(msg)

     