web: daphne zcl.asgi:application --port $PORT --bind 0.0.0.0
worker: celery -A zcl.celery worker --logl=info --concurrency=3
