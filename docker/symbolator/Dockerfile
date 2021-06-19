FROM ubuntu:20.04
# docker build --build-arg LIBRARY_VERSION=0.0.1 -t quay.io/buildsi/symbolator:0.0.1
ENV DEBIAN_FRONTEND=noninteractive
ARG LIBRARY_VERSION=0.0.13
ENV LIBRARY_VERSION=${LIBRARY_VERSION}
RUN apt-get update && apt-get install -y git \
    python3 \
    python3-dev \
    python3-pip

RUN pip install symbolator-python==${LIBRARY_VERSION} && \
    pip install pytest
