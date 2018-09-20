web: gunicorn wc2018.wsgi
worker: celery -A wc2018 worker
beat: celery -A wc2018 beat -S django