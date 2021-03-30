FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN set -eu; \
    apt-get update; \
    apt-get install -yq \
        fontconfig \
        fonts-dejavu \
        imagemagick \
        libcairo2-dev \
        pkg-config \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
        python3-virtualenv \
        python3-virtualenvwrapper \
        ttf-aenigma \
        ttf-bitstream-vera \
        ; \
    apt-get clean;

RUN mkdir /venv; python3 -m venv /venv

COPY requirements.txt /tmp/
RUN /venv/bin/pip install -r /tmp/requirements.txt

ENV LANG=en_US.utf8
