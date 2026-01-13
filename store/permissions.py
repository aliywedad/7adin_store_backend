# permissions.py
from rest_framework.permissions import BasePermission

from store.models import Users

class HasTokenPermission(BasePermission):

    def has_permission(self, request, view):
        print("Checking permissions for request: ",request)
        return True
        auth_header = request.headers.get('Authorization')
        if auth_header :
            token = auth_header.split(' ')[1]
            user = Users.objects.filter(token=token).first()
            if user:
                print("user ",user)
                return True
            
            
    
        return False
