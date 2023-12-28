from decouple import config
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a superuser.'

    def handle(self, *args, **options):
        if not User.objects.filter(email=config('ADMIN_EMAIL')).exists():
            User.objects.create_superuser(
                email=config('ADMIN_EMAIL'),
                first_name='Admin',
                last_name='user',
                phone_number='+1234567890',
                password=config('ADMIN_PASSWORD')
            )
            print('Superuser has been created.')
        else:
            print("Superuser already exists.")
