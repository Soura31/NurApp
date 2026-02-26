import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure a superuser exists based on env vars."

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "").strip()
        email = os.getenv("ADMIN_EMAIL", "").strip()

        if not username or not password:
            self.stdout.write("ADMIN_USERNAME/ADMIN_PASSWORD not set; skip ensure_admin.")
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' already exists.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
