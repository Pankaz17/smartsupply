from django.core.management.base import BaseCommand

from apps.analytics.services import run_nightly_analytics


class Command(BaseCommand):
    help = 'Run nightly analytics: supplier metrics, dead stock, recommendations.'

    def handle(self, *args, **options):
        summary = run_nightly_analytics()
        rec_total = summary['recommendations_created'] + summary['recommendations_updated']

        self.stdout.write(self.style.SUCCESS(
            f'Processed:\n'
            f'  * {summary["products_processed"]} Products\n'
            f'  * {summary["suppliers_processed"]} Suppliers\n'
            f'  * {rec_total} Recommendations Generated\n'
            f'  * {summary["dead_stock_flagged"]} Dead Stock Items\n'
            f'  * {summary["supplier_snapshots_updated"]} Supplier Snapshots Updated\n'
            f'  * {summary["active_seasonal_events"]} Active Seasonal Events',
        ))
