#!/bin/bash
set -e

# Manual install wahi_korero
cd /webapp/corpora/corpora/
curl -L -o wahi_korero.tar.gz https://github.com/TeHikuMedia/wahi-korero/archive/v0.5.1.tar.gz 
tar -xzvf wahi_korero.tar.gz
mv wahi-korero-0.5.1/wahi_korero/ wahi_korero || true
rm wahi_korero.tar.gz
rm -r wahi-korero-0.5.1

python /webapp/corpora/corpora/manage.py compilemessages
python /webapp/corpora/corpora/manage.py migrate --noinput
python /webapp/corpora/corpora/manage.py collectstatic --clear --noinput 
python /webapp/corpora/corpora/manage.py loaddata /webapp/corpora/corpora/people/fixtures/iwi.yaml
python /webapp/corpora/corpora/manage.py shell -c "from django.db import DEFAULT_DB_ALIAS as database; from django.contrib import auth; model = auth.get_user_model(); model.objects.db_manager(database).create_superuser('docker','docker@email.com', 'password')" || true


exec "$@"