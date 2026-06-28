from decimal import Decimal

from django.test import TestCase

from apps.purchasing.models import ReorderRecommendation
from apps.purchasing.priority import (
    assign_priority_levels,
    calculate_expected_restock_profit,
    calculate_priority_score,
    calculate_profit_metrics,
    calculate_unit_profit,
)
from common.test_utils import create_category, create_owner, create_product, create_supplier


class ProfitCalculationTests(TestCase):
    def test_unit_profit(self):
        self.assertEqual(
            calculate_unit_profit(Decimal('10.00'), Decimal('6.00')),
            Decimal('4.00'),
        )

    def test_priority_score(self):
        score = calculate_priority_score(Decimal('4.00'), Decimal('2.50'))
        self.assertEqual(score, Decimal('10.00'))

    def test_expected_restock_profit(self):
        profit = calculate_expected_restock_profit(Decimal('4.00'), 10)
        self.assertEqual(profit, Decimal('40.00'))

    def test_calculate_profit_metrics(self):
        product = create_product(
            cost_price=Decimal('5.00'),
            selling_price=Decimal('12.00'),
        )
        unit_profit, priority_score, expected = calculate_profit_metrics(
            product, Decimal('3.00'), 8,
        )
        self.assertEqual(unit_profit, Decimal('7.00'))
        self.assertEqual(priority_score, Decimal('21.00'))
        self.assertEqual(expected, Decimal('56.00'))


class PriorityLevelTests(TestCase):
    def _make_rec(self, score):
        rec = ReorderRecommendation(priority_score=Decimal(score))
        return rec

    def test_single_recommendation_is_high(self):
        recs = [self._make_rec('10')]
        assign_priority_levels(recs)
        self.assertEqual(recs[0].priority_level, ReorderRecommendation.PriorityLevel.HIGH)

    def test_quartile_assignment_for_four_items(self):
        recs = [
            self._make_rec('40'),
            self._make_rec('30'),
            self._make_rec('20'),
            self._make_rec('10'),
        ]
        assign_priority_levels(recs)
        levels = {r.priority_score: r.priority_level for r in recs}
        self.assertEqual(levels[Decimal('40')], ReorderRecommendation.PriorityLevel.HIGH)
        self.assertEqual(levels[Decimal('30')], ReorderRecommendation.PriorityLevel.MEDIUM)
        self.assertEqual(levels[Decimal('20')], ReorderRecommendation.PriorityLevel.MEDIUM)
        self.assertEqual(levels[Decimal('10')], ReorderRecommendation.PriorityLevel.LOW)


class RecommendationOrderingTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        supplier = create_supplier()
        category = create_category()

        self.high = create_product(
            sku='HIGH-MARGIN',
            name='Premium Juice',
            supplier=supplier,
            category=category,
            cost_price=Decimal('2.00'),
            selling_price=Decimal('10.00'),
            stock=0,
        )
        self.low = create_product(
            sku='LOW-MARGIN',
            name='Basic Water',
            supplier=supplier,
            category=category,
            cost_price=Decimal('0.90'),
            selling_price=Decimal('1.00'),
            stock=0,
        )

        ReorderRecommendation.objects.create(
            product=self.high,
            supplier=supplier,
            current_stock=0,
            recommended_quantity=10,
            average_daily_sales=Decimal('5.00'),
            lead_time_days=5,
            safety_stock=Decimal('15.00'),
            calculated_reorder_point=Decimal('40.00'),
            unit_profit=Decimal('8.00'),
            priority_score=Decimal('40.00'),
            expected_restock_profit=Decimal('80.00'),
            priority_level=ReorderRecommendation.PriorityLevel.HIGH,
            status=ReorderRecommendation.Status.PENDING,
            reason='Test',
        )
        ReorderRecommendation.objects.create(
            product=self.low,
            supplier=supplier,
            current_stock=0,
            recommended_quantity=10,
            average_daily_sales=Decimal('5.00'),
            lead_time_days=5,
            safety_stock=Decimal('15.00'),
            calculated_reorder_point=Decimal('40.00'),
            unit_profit=Decimal('0.10'),
            priority_score=Decimal('0.50'),
            expected_restock_profit=Decimal('1.00'),
            priority_level=ReorderRecommendation.PriorityLevel.LOW,
            status=ReorderRecommendation.Status.PENDING,
            reason='Test',
        )

    def test_default_ordering_by_priority_score(self):
        recs = list(ReorderRecommendation.objects.all())
        self.assertEqual(recs[0].product.sku, 'HIGH-MARGIN')
        self.assertEqual(recs[1].product.sku, 'LOW-MARGIN')
