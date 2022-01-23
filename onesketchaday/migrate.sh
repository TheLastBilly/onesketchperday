#!/bin/bash

/venv/bin/python manage.py makemigrations app
/venv/bin/python manage.py migrate --run-syncdb