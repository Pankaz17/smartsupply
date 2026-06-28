from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from common.permissions import IsOwner

from .models import User
from .serializers import (
    PasswordChangeSerializer,
    StaffCreateSerializer,
    StaffUpdateSerializer,
    UserSerializer,
)
from .tokens import SmartSupplyTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = SmartSupplyTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class PasswordChangeView(APIView):
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Password updated successfully.'})


class StaffListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return User.objects.filter(role=User.Role.STAFF).order_by('email')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StaffCreateSerializer
        return UserSerializer


class StaffDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsOwner,)
    serializer_class = StaffUpdateSerializer

    def get_queryset(self):
        return User.objects.filter(role=User.Role.STAFF)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return StaffUpdateSerializer
