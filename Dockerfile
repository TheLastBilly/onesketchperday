FROM python

ENV DEFAULT_PASSWORD=pass
ENV APP_NAME=onesketchaday

ENV WORKERS=3
ENV PUID=1000
ENV PGID=1000

ENV DB_NAME=onesketchaday
ENV DB_USER=user
ENV DB_PASSWORD=pass
ENV DB_HOST=db
ENV DB_PORT=3306

ENV USE_SOCKET=1

ENV DEBIAN_FRONTEND noninteractive

RUN apt update
RUN apt install -y postgresql-client libmariadb-dev
RUN apt-get autoremove

COPY ./requirements.txt /tmp/
RUN python3 -m pip install -r /tmp/requirements.txt

COPY ./$APP_NAME /$APP_NAME
WORKDIR /$APP_NAME
RUN rm -f /$APP_NAME/telegram-token
RUN rm -f /$APP_NAME/django-token
RUN rm -f  /$APP_NAME/db.sqlite3

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD /entrypoint.sh