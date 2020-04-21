FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qq -y update \
    && apt-get -qq -y install \
        python3 python3-icu python3-pip python3-psycopg2 python3-pandas python3-numpy \
        postgresql-client-12 curl wget locales libpq-dev && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

COPY requirements.txt /tmp/
RUN pip3 install \
    networkx==2.4 \
    python-Levenshtein==0.12.0 \
    normality==2.0.0 \
    click \
    rdflib \
    dataset \
    pgcli
RUN mkdir /synonames
WORKDIR /synonames
COPY src/ Makefile requirements.txt /synonames/

ENV DATABASE_URI postgresql://db:db@db/db