from django.core.management.base import BaseCommand

from apps.accounts.models import BusinessSettings, User


class Command(BaseCommand):
    help = 'Create the initial owner account and default business settings.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Owner email address')
        parser.add_argument('--password', required=True, help='Owner password')
        parser.add_argument('--name', default='', help='Owner full name')
        parser.add_argument('--store', default='My Store', help='Store name')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        full_name = options['name'] or email.split('@')[0]
        store_name = options['store']

        if User.objects.filter(role=User.Role.OWNER).exists():
            self.stderr.write(self.style.WARNING('An owner account already exists.'))
            return

        User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=User.Role.OWNER,
        )

        settings = BusinessSettings.get_solo()
        settings.store_name = store_name
        settings.save()

        self.stdout.write(self.style.SUCCESS(f'Owner created: {email}'))
        self.stdout.write(self.style.SUCCESS(f'Store configured: {store_name}'))
