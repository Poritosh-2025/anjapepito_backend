import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cleanup-expired-otps": {
        "task": "apps.authentication.tasks.cleanup_expired_otps",
        "schedule": crontab(minute="*/5"),
    },
    "cleanup-expired-reset-tokens": {
        "task": "apps.authentication.tasks.cleanup_expired_reset_tokens",
        "schedule": crontab(minute="*/15"),
    },
    "cleanup-blacklisted-tokens": {
        "task": "apps.authentication.tasks.cleanup_blacklisted_tokens",
        "schedule": crontab(hour=3, minute=0),
    },
}
