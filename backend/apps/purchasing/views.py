from django.core.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwner, IsOwnerOrReadOnly

from .models import PurchaseOrder, ReorderRecommendation
from .serializers import (
    PurchaseOrderCreateSerializer,
    PurchaseOrderDetailSerializer,
    PurchaseOrderListSerializer,
    PurchaseOrderStatusSerializer,
    ReorderRecommendationSerializer,
)
from .operational_priority import order_by_operational_priority
from .services import approve_recommendation, dismiss_recommendation, generate_recommendations


class ReorderRecommendationListView(generics.ListAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = ReorderRecommendationSerializer

    def get_queryset(self):
        qs = ReorderRecommendation.objects.select_related(
            'product', 'supplier', 'purchase_order',
        ).all()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return order_by_operational_priority(qs)


class GenerateRecommendationsView(APIView):
    permission_classes = (IsOwner,)

    def post(self, request):
        results = generate_recommendations()
        return Response({
            'detail': 'Recommendations generated.',
            **results,
        })


class ApproveRecommendationView(APIView):
    permission_classes = (IsOwner,)

    def post(self, request, pk):
        try:
            recommendation = ReorderRecommendation.objects.select_related(
                'product', 'supplier',
            ).get(pk=pk)
        except ReorderRecommendation.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            po = approve_recommendation(recommendation, request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': 'Recommendation approved. Draft purchase order created.',
            'recommendation': ReorderRecommendationSerializer(recommendation).data,
            'purchase_order_id': po.id,
            'po_number': po.po_number,
        })


class DismissRecommendationView(APIView):
    permission_classes = (IsOwner,)

    def post(self, request, pk):
        try:
            recommendation = ReorderRecommendation.objects.get(pk=pk)
        except ReorderRecommendation.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            dismiss_recommendation(recommendation)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': 'Recommendation dismissed.',
            'recommendation': ReorderRecommendationSerializer(recommendation).data,
        })


class PurchaseOrderListView(generics.ListCreateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related('supplier', 'created_by').all()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PurchaseOrderCreateSerializer
        return PurchaseOrderListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = serializer.save()
        detail = PurchaseOrderDetailSerializer(
            PurchaseOrder.objects.select_related(
                'supplier', 'created_by', 'approved_by',
            ).prefetch_related('items__product').get(pk=po.pk),
        )
        return Response(detail.data, status=status.HTTP_201_CREATED)


class PurchaseOrderDetailView(generics.RetrieveAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = PurchaseOrderDetailSerializer

    def get_queryset(self):
        return PurchaseOrder.objects.select_related(
            'supplier', 'created_by', 'approved_by',
        ).prefetch_related('items__product')


class PurchaseOrderStatusView(APIView):
    permission_classes = (IsOwner,)

    def patch(self, request, pk):
        try:
            po = PurchaseOrder.objects.select_related('supplier').get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PurchaseOrderStatusSerializer(
            data=request.data,
            context={'purchase_order': po},
        )
        serializer.is_valid(raise_exception=True)

        try:
            po.transition_status(
                serializer.validated_data['status'],
                request.user,
                actual_delivery_date=serializer.validated_data.get('actual_delivery_date'),
            )
        except ValidationError as exc:
            return Response({'detail': exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

        po = PurchaseOrder.objects.select_related(
            'supplier', 'created_by', 'approved_by',
        ).prefetch_related('items__product').get(pk=pk)

        return Response({
            'detail': f'Purchase order status updated to {po.status}.',
            'purchase_order': PurchaseOrderDetailSerializer(po).data,
        })
