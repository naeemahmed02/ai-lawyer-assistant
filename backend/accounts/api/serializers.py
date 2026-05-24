from rest_framework import serializers
from django.contrib.auth import authenticate
from ..models import Account

class UserSerialier(serializers.ModelSerializer):
    
    class Meta:
        model = Account
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'username',
            'phone_number',
            'role',
            'is_active',
            'is_staff',
            'date_joined',
        )
        
        read_only_fields = ['id', 'date_joined']