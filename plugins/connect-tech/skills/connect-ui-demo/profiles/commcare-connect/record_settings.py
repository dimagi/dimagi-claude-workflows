"""Out-of-repo Django settings for demo recordings. Loaded via PYTHONPATH + DJANGO_SETTINGS_MODULE=record_settings.

- DEBUG off → no Debug Toolbar in frame (local.py hardcodes DEBUG = True, so the env var alone does nothing).
- Email always goes to the console (output/server.log), even if .env points DJANGO_EMAIL_BACKEND at a real SMTP
  server — a demo must never send mail to the seeded addresses. Demos do not show email on camera.
- Celery is already eager in local.py, so emails sent via tasks fire inline without a worker.
"""
from config.settings.local import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = list({*ALLOWED_HOSTS, "localhost", "127.0.0.1"})  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
