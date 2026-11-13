from django.core import mail
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Verify database, private-media access, and SMTP authentication without sending mail.'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            raise CommandError('Database connectivity verification failed.') from None
        try:
            # HEAD of a nonexistent object checks credentials without writing a file.
            default_storage.exists('system/toolx-connectivity-check')
        except Exception:
            raise CommandError('Private media connectivity verification failed.') from None
        backend = mail.get_connection()
        try:
            backend.open()
        except Exception:
            raise CommandError('SMTP authentication verification failed.') from None
        finally:
            backend.close()
        self.stdout.write(self.style.SUCCESS('Database, private media, and SMTP authentication verified. No email sent.'))
