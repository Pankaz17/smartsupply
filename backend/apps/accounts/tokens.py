from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import UserSerializer


class SmartSupplyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            from rest_framework import serializers
            raise serializers.ValidationError('This account has been deactivated.')
        data['user'] = UserSerializer(self.user).data
        return data
