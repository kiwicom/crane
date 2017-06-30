FROM python:3-alpine

MAINTAINER Simone Esposito <simone@kiwi.com>

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app
RUN apk add --no-cache --virtual=.run-deps git &&\
    pip install -r requirements.txt

COPY . /app

RUN python setup.py install

CMD ["crane"]
LABEL name=crane version=dev
