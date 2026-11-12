import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction

from instant_generator.models import Profile


class Command(BaseCommand):
    help = 'Create the initial administrator from environment variables, without changing existing accounts.'

    def handle(self, *args, **options):
        if os.environ.get('TOOLX_BOOTSTRAP_ADMIN', '').lower() not in ('1', 'true', 'yes'):
            return
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip().lower()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if not all((username, email, password)):
            raise CommandError('Initial administrator configuration is incomplete.')
        User = get_user_model()
        with transaction.atomic():
            existing = User.objects.select_for_update().filter(username=username).first()
            if existing:
                if existing.email.lower() != email or not (existing.is_superuser and existing.is_staff and existing.is_active):
                    raise CommandError('Initial administrator identity conflicts with an existing account; no account was modified.')
                self.stdout.write('Administrator already initialized; credentials were not changed.')
                return
            if User.objects.filter(email__iexact=email).exists():
                raise CommandError('Initial administrator email already belongs to an account; no account was modified.')
            candidate = User(username=username, email=email)
            try:
                validate_email(email)
                candidate.full_clean(exclude=['password', 'last_login', 'date_joined'])
                validate_password(password, user=candidate)
            except ValidationError:
                raise CommandError('Initial administrator identity or password does not meet validation requirements.') from None
            user = User.objects.create_superuser(username=username, email=email, password=password)
            Profile.objects.filter(user=user).update(activation_pending=False, email_confirmed=True)
        self.stdout.write(self.style.SUCCESS('Initial administrator created.'))
