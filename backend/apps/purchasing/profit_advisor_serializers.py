from decimal import Decimal

from rest_framework import serializers


class ProfitAdvisorRequestSerializer(serializers.Serializer):
    budget = serializers.DecimalField(max_digits=14, decimal_places=2)

    def validate_budget(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('Budget must be greater than zero.')
        return value
