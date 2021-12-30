#!/bin/bash

chown -R $PUID:$PGID /$APP_NAME
cd /$APP_NAME

BIND=""
if [ "$USE_SOCKET" == "1" ]; then
    BIND="--bind unix:/tmp/$APP_NAME.sock"
else
    BIND=""
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

gunicorn --user=$PUID --group=$PGID --workers $WORKERS $BIND $APP_NAME.wsgi