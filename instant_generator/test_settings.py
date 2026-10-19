import os
import subprocess
import sys

from django.test import SimpleTestCase


class ProductionConfigurationTests(SimpleTestCase):
    def check_settings(self, **overrides):
        env = {**os.environ, 'DEBUG': 'False',
               'SECRET_KEY': 'settings-test-only-0123456789abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLM',
               'ALLOWED_HOSTS': 'toolx.example.com', 'PUBLIC_ORIGIN': 'https://toolx.example.com',
               'DATABASE_URL': 'postgresql://test:test@localhost:5432/toolx',
               'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
               'EMAIL_HOST': 'smtp.example.com', 'EMAIL_USE_TLS': 'True', 'EMAIL_USE_SSL': 'False',
               'ADMIN_EMAIL': 'noreply@toolx.example.com', 'AWS_STORAGE_BUCKET_NAME': 'test-only',
               'AWS_S3_REGION_NAME': 'us-east-1', **overrides}
        return subprocess.run([sys.executable, '-c', 'import toolx.settings'], env=env, capture_output=True, text=True)

    def test_exact_origin_and_hosts_are_accepted(self):
        self.assertEqual(self.check_settings().returncode, 0)

    def test_wildcards_and_subdomain_patterns_are_rejected(self):
        for host in ('*', '.example.com', '*.example.com', 'https://toolx.example.com', 'toolx.example.com:443'):
            with self.subTest(host=host):
                result = self.check_settings(ALLOWED_HOSTS=host)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('exact deployment hostnames', result.stderr)

    def test_mismatched_origin_and_invalid_ports_are_rejected(self):
        result = self.check_settings(PUBLIC_ORIGIN='https://other.example.com')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('hostname must be included', result.stderr)
        for port in ('invalid', '99999'):
            result = self.check_settings(PUBLIC_ORIGIN='https://toolx.example.com:' + port)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('invalid port', result.stderr)
