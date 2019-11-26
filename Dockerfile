FROM ubuntu
RUN apt-get update && apt-get install -y python3 python3-icu python3-pip curl wget postgresql-client locales libpq-dev
ENV DEBIAN_FRONTEND noninteractive

# Set up the locale and make sure the system uses unicode for the file system.
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure locales \
    && update-locale LANG=en_US.UTF-8
ENV LANG='en_US.UTF-8' \
    LC_ALL='en_US.UTF-8'

RUN mkdir /code
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
WORKDIR /code
COPY code/ Makefile requirements.txt /code/

ENV DATABASE_URI postgresql://db:db@db/db