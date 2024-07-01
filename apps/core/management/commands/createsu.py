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
                password=config('ADMIN_PASSWORD')
            )
            self.stdout.write(self.style.SUCCESS('Superuser has been created.'))
        else:
            self.stderr.write(self.style.WARNING("Superuser already exists."))
