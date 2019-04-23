FROM postgres:11-alpine

COPY *.sql /docker-entrypoint-initdb.d/

USER postgres
RUN initdb
