# O Railway NÃO roda a linha "release:" automaticamente como o Heroku faz.
# migrate vira "Pre-Deploy Command" no serviço "web" (Settings > Deploy) -
# escreve no Postgres externo, então persiste normalmente. collectstatic
# NÃO pode ir no Pre-Deploy Command: esse passo roda num container efêmero
# separado do que efetivamente fica no ar, então qualquer escrita em disco
# local (como os arquivos estáticos coletados) se perde - por isso
# collectstatic entra direto no comando de start abaixo. Ver README.
web: python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 30
worker: celery -A config worker --loglevel=info --concurrency=2
beat: celery -A config beat --loglevel=info
