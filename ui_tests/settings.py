import os
from toolx.settings import *  # noqa: F403

# Browser checks always use a disposable database selected by their runner.
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': os.environ['UI_TEST_DB']}}
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PUBLIC_ORIGIN = 'http://127.0.0.1:4173'
