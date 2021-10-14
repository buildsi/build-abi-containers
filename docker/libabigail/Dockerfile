FROM ubuntu:20.04

# docker build --build-arg LIBRARY_VERSION=2.0 -t ghcr.io/buildsi/libabigail:2.0 .

ENV DEBIAN_FRONTEND=noninteractive
ARG LIBRARY_VERSION=2.0
RUN apt-get update && apt-get install -y build-essential \
    curl \
    libelf-dev \
    libzip-dev \
    autoconf \
    libtool \
    pkg-config \
    libxml2 \
    libxml2-dev \
    elfutils \
    doxygen \
    wget \
    git \
    libdw-dev \
    elfutils \
    python3-lxml \
    python3 \
    python3-dev \
    python3-sphinx \
    python3-pip

RUN ldconfig && \ 
    wget http://mirrors.kernel.org/sourceware/libabigail/libabigail-${LIBRARY_VERSION}.tar.gz && \
    tar -xvf libabigail-${LIBRARY_VERSION}.tar.gz && \
    cd libabigail-${LIBRARY_VERSION} && \
    autoreconf -fi && \
    mkdir build && \
    cd build && \
    ../configure --prefix=/usr/local && \
    make all install && \
    ldconfig && \
    pip install pytest

