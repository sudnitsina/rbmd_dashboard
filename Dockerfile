FROM python:2.7-alpine3.8

MAINTAINER Anna Sudnitsyna

EXPOSE 8000

WORKDIR /usr/src/app
COPY requirements.txt ./

RUN apk update && apk add gcc musl-dev libffi-dev openssl-dev python3-dev sqlite
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ADD entrypoint.sh /

ENTRYPOINT /entrypoint.sh