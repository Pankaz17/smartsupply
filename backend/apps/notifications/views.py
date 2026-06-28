import django_filters
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwnerOrStaff

from .models import Notification
from .serializers import NotificationSerializer
from .services import get_unread_count, mark_all_read


class NotificationFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(field_name='notification_type')
    is_read = django_filters.BooleanFilter()

    class Meta:
        model = Notification
        fields = ['type', 'is_read']


class NotificationListView(generics.ListAPIView):
    permission_classes = (IsOwnerOrStaff,)
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter

    def get_queryset(self):
        return Notification.objects.select_related(
            'related_product', 'related_supplier', 'related_purchase_order',
        ).all()


class NotificationUnreadCountView(APIView):
    permission_classes = (IsOwnerOrStaff,)

    def get(self, request):
        return Response({'unread_count': get_unread_count()})


class NotificationMarkReadView(APIView):
    permission_classes = (IsOwnerOrStaff,)

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        notification.mark_read()
        return Response({
            'detail': 'Notification marked as read.',
            'notification': NotificationSerializer(notification).data,
        })


class NotificationMarkAllReadView(APIView):
    permission_classes = (IsOwnerOrStaff,)

    def post(self, request):
        updated = mark_all_read()
        return Response({
            'detail': f'{updated} notification(s) marked as read.',
            'unread_count': get_unread_count(),
        })
