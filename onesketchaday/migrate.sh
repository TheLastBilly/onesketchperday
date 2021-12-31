#!/bin/bash

python3 manage.py makemigrations app
python3 manage.py migrate --run-syncdb