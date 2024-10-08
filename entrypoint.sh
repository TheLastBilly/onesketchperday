#!/bin/bash

chown -R $PUID:$PGID /$APP_NAME
cd /$APP_NAME

BIND=""
if [ "$USE_SOCKET" == "1" ]; then
    mkdir /sockets/
    BIND="--bind unix:/sockets/$APP_NAME.sock"
else
    BIND="--bind 0.0.0.0:8000"
fi

if [ ! -f /config/initialized ]; then
    /$APP_NAME/setupdb.sh
    A="$?"
    B="$?"
    if [ $A -eq 0 ] && [ $B -eq 0 ]; then
        touch /config/initialized
    fi
fi

if [ -f /config/migrate_database ]; then
    ./migrate.sh
    if [ $? -eq 0 ]; then
        rm /config/migrate_database
    fi
fi

rm -rf static/*
/venv/bin/python manage.py collectstatic

groupadd -g $PGID app
useradd -u $PUID -g $PGID app

# Discord bot no longer needed
/venv/bin/python manage.py discord_bot &

/venv/bin/gunicorn --user $PUID --group $PGID --workers $WORKERS $BIND $APP_NAME.wsgi