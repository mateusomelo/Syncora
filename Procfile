# O Railway NÃO roda a linha "release:" automaticamente como o Heroku faz -
# migrations + collectstatic são configurados como "Pre-Deploy Command" no
# serviço "web" (Settings > Deploy), rodando só uma vez ali (não em todos os
# serviços, pra evitar migração concorrente). Ver README, seção de deploy.
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 30
worker: celery -A config worker --loglevel=info --concurrency=2
beat: celery -A config beat --loglevel=info
