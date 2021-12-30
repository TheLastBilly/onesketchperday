#!/bin/bash

if [ -f ./db.sqlite3 ]; then
    echo "Previous cache of db.sqlite3 found, deleting..."
    rm -rf ./db.sqlite3
fi

python3 manage.py makemigrations app
python3 manage.py migrate --run-syncdb

if [[ -z "$DEFAULT_PASSWORD" ]]; then
    DEFAULT_PASSWORD=pass
fi

cat << EOF | python manage.py shell
from app.models import *
from django.utils import timezone

User.objects.create_superuser('admin', 'adminId', '$DEFAULT_PASSWORD')

MardownPost.objects.create(title='About',contents='# About')
Variable.objects.create(name='StartDate', date=timezone.now())
EOF