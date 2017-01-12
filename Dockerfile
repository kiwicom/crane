FROM python:3-alpine

MAINTAINER Simone Esposito <simone@kiwi.com>

RUN mkdir /app
WORKDIR /app

COPY . /app

RUN python setup.py install

CMD ["advance"]
LABEL name=advance version=dev
