from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsOwner

from .models import BusinessSettings
from .serializers import BusinessSettingsSerializer


class BusinessSettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BusinessSettingsSerializer

    def get_object(self):
        return BusinessSettings.get_solo()

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsOwner()]
        return [IsAuthenticated()]
