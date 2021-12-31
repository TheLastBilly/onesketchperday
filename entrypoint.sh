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

if [ ! -f /config/done ]; then
    /$APP_NAME/setupDB.sh
    A="$?"
    python manage.py collectstatic
    B="$?"
    if [ $A -eq 0 ] && [ $B -eq 0 ]; then
        touch /config/done
    fi
fi

groupadd -g $PGID app
useradd -u $PUID -g $PGID app

python manage.py startbot &
gunicorn --user $PUID --group $PGID --workers $WORKERS $BIND $APP_NAME.wsgi