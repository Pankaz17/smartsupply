from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.exports import build_export_response
from common.permissions import IsOwner, IsOwnerOrStaff

from .profit_advisor import (
    get_latest_profit_advisor_analysis,
    run_profit_advisor_analysis,
    save_profit_advisor_analysis,
)
from .profit_advisor_serializers import ProfitAdvisorRequestSerializer

EXPORT_COLUMNS = [
    {'key': 'product', 'label': 'Product'},
    {'key': 'unit_profit', 'label': 'Unit Profit'},
    {'key': 'purchase_cost', 'label': 'Purchase Cost'},
    {'key': 'expected_profit', 'label': 'Expected Profit'},
    {'key': 'priority_score', 'label': 'Financial Priority Score'},
    {'key': 'decision', 'label': 'Decision'},
]


class ProfitAdvisorView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsOwner()]
        return [IsOwnerOrStaff()]

    def get(self, request):
        analysis = get_latest_profit_advisor_analysis()
        if not analysis:
            return Response({'has_analysis': False})
        return Response({'has_analysis': True, **analysis})

    def post(self, request):
        serializer = ProfitAdvisorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        budget = serializer.validated_data['budget']

        analysis = run_profit_advisor_analysis(budget)
        save_profit_advisor_analysis(request.user, analysis)

        return Response(analysis, status=status.HTTP_200_OK)


class ProfitAdvisorExportView(APIView):
    permission_classes = (IsOwnerOrStaff,)

    def get(self, request):
        analysis = get_latest_profit_advisor_analysis()
        if not analysis:
            return Response(
                {'detail': 'No Profit Advisor analysis available to export.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        fmt = request.query_params.get('export_format', 'csv')
        if fmt not in ('csv', 'xlsx'):
            return Response({'detail': 'export_format must be csv or xlsx.'}, status=400)

        rows = [
            {**row, 'decision': 'Recommended'}
            for row in analysis['recommended_products']
        ] + [
            {**row, 'decision': 'Deferred'}
            for row in analysis['deferred_products']
        ]

        summary = {
            'budget': analysis['budget'],
            'recommended_spending': analysis['recommended_spending'],
            'remaining_budget': analysis['remaining_budget'],
            'expected_profit': analysis['expected_profit'],
            'recommended_count': analysis['recommended_count'],
        }

        return build_export_response(
            fmt,
            'profit_advisor_analysis',
            EXPORT_COLUMNS,
            rows,
            summary,
        )
