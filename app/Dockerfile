FROM python:3-alpine

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

WORKDIR /usr/src/app

RUN pip install --no-cache-dir psycopg2 config configparser

CMD ["python", "./main.py"]
