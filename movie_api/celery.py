import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_api.settings')

app = Celery('movie_api')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'update-movie-cache': {
        'task': 'movies.tasks.update_movie_cache',
        'schedule': 3600.0,  # Run every hour
    },
    'cleanup-expired-cache': {
        'task': 'movies.tasks.cleanup_expired_cache',
        'schedule': 86400.0,  # Run daily
    },
    'update-recommendations': {
        'task': 'recommendations.tasks.update_user_recommendations',
        'schedule': 21600.0,  # Run every 6 hours
    },
    'calculate-similarities': {
        'task': 'recommendations.tasks.calculate_user_similarities',
        'schedule': 43200.0,  # Run every 12 hours
    },
}

app.conf.timezone = 'UTC'