import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

User = get_user_model()


class BootstrapAdminTests(TestCase):
    def setUp(self):
        self.env = {'TOOLX_BOOTSTRAP_ADMIN': 'true', 'DJANGO_SUPERUSER_USERNAME': 'initialadmin',
                    'DJANGO_SUPERUSER_EMAIL': 'admin@example.com', 'DJANGO_SUPERUSER_PASSWORD': 'StrongInitialPass123!'}

    def run_command(self, env=None):
        out = StringIO()
        with patch.dict(os.environ, self.env if env is None else env):
            call_command('bootstrap_admin', stdout=out)
        self.assertNotIn(self.env['DJANGO_SUPERUSER_PASSWORD'], out.getvalue())
        return out.getvalue()

    def test_initial_account_is_ready_for_login_and_administration(self):
        self.run_command()
        user = User.objects.get(username='initialadmin')
        self.assertTrue(user.is_superuser and user.is_staff and user.is_active)
        self.assertTrue(user.profile.email_confirmed)
        self.assertFalse(user.profile.activation_pending)
        self.assertTrue(self.client.login(username='initialadmin', password=self.env['DJANGO_SUPERUSER_PASSWORD']))
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_redeploy_does_not_reset_changed_password(self):
        self.run_command()
        user = User.objects.get(username='initialadmin')
        user.set_password('ChangedStrongPass123!')
        user.save()
        self.run_command()
        user.refresh_from_db()
        self.assertTrue(user.check_password('ChangedStrongPass123!'))

    def test_conflicting_regular_user_is_never_promoted(self):
        user = User.objects.create_user('initialadmin', email='admin@example.com')
        with self.assertRaises(CommandError): self.run_command()
        user.refresh_from_db()
        self.assertFalse(user.is_superuser or user.is_staff)

    def test_conflicting_email_does_not_create_another_identity(self):
        User.objects.create_user('existing', email='Admin@example.com')
        with self.assertRaises(CommandError): self.run_command()
        self.assertEqual(User.objects.count(), 1)

    def test_missing_and_weak_configuration_fail_without_creating_user(self):
        for changes in ({'DJANGO_SUPERUSER_PASSWORD': ''}, {'DJANGO_SUPERUSER_PASSWORD': 'short'}, {'DJANGO_SUPERUSER_EMAIL': 'invalid'}):
            with self.assertRaises(CommandError): self.run_command({**self.env, **changes})
        self.assertEqual(User.objects.count(), 0)

    def test_bootstrap_is_opt_in(self):
        self.run_command({**self.env, 'TOOLX_BOOTSTRAP_ADMIN': 'false'})
        self.assertFalse(User.objects.exists())

    def test_external_service_checks_never_send_mail_or_expose_provider_errors(self):
        from unittest.mock import MagicMock
        backend = MagicMock()
        with patch('instant_generator.management.commands.check_external_services.default_storage.exists', return_value=False), patch('instant_generator.management.commands.check_external_services.mail.get_connection', return_value=backend):
            call_command('check_external_services', stdout=StringIO())
        backend.open.assert_called_once()
        backend.close.assert_called_once()
        backend.send_messages.assert_not_called()
        with patch('instant_generator.management.commands.check_external_services.default_storage.exists', side_effect=RuntimeError('sensitive provider details')):
            with self.assertRaisesMessage(CommandError, 'Private media connectivity verification failed.') as caught:
                call_command('check_external_services', stdout=StringIO())
        self.assertNotIn('sensitive provider details', str(caught.exception))
