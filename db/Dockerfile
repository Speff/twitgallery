FROM postgres:11-alpine
EXPOSE 5432

COPY *.sql /docker-entrypoint-initdb.d/

USER postgres
RUN initdb
