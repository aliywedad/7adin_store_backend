# permissions.py
from rest_framework.permissions import BasePermission

from store.models import Users

class HasTokenPermission(BasePermission):
    
    """
    Allows access only if the request has an Authorization header with a token.
    """

    def has_permission(self, request, view):
        return True
        auth_header = request.headers.get('Authorization')
        if auth_header :
            token = auth_header.split(' ')[1]
            print("token : ",token)
            user = Users.objects.filter(token=token).first()
            print(user)
            if user:
                print("user exists")
                return True
            
            
    
        return False
