from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError


def parse_date_range(query_params, default_days=30):
    """
    Parse report date range from query params.

    Supports:
      - range=7d | 30d | 90d
      - start_date & end_date (YYYY-MM-DD)

    Raises ValidationError for invalid input (never raises unhandled exceptions).
    """
    today = timezone.now().date()
    start_str = query_params.get('start_date')
    end_str = query_params.get('end_date')
    range_param = query_params.get('range', f'{default_days}d')

    if start_str or end_str:
        if not start_str or not end_str:
            raise ValidationError({
                'date_range': 'Both start_date and end_date are required for a custom range.',
            })
        try:
            start = datetime.strptime(start_str, '%Y-%m-%d').date()
            end = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError({
                'date_range': 'Invalid date format. Use YYYY-MM-DD.',
            })
        if start > end:
            raise ValidationError({
                'date_range': 'start_date must be on or before end_date.',
            })
        return start, end, 'custom'

    days_map = {'7d': 7, '30d': 30, '90d': 90}
    if range_param not in days_map:
        raise ValidationError({
            'range': 'Invalid range. Use 7d, 30d, or 90d.',
        })
    days = days_map[range_param]
    start = today - timedelta(days=days)
    return start, today, range_param
