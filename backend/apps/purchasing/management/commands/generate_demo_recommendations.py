from django.core.management.base import BaseCommand

from apps.purchasing.services import generate_recommendations


class Command(BaseCommand):
    help = 'Generate demo reorder recommendations based on current inventory and sales.'

    def handle(self, *args, **options):
        results = generate_recommendations()
        self.stdout.write(self.style.SUCCESS(
            f'Recommendations generated — created: {results["created"]}, '
            f'updated: {results["updated"]}, skipped: {results["skipped"]}.',
        ))
