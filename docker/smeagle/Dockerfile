FROM ghcr.io/autamus/dyninst:master
# docker build -t ghcr.io/buildsi/smeagle:0.0.0 .
ENV DEBIAN_FRONTEND=noninteractive
ARG LIBRARY_VERSION=0.0.0
RUN apt-get update && \
    apt-get install -y wget g++ libssl-dev libtbb-dev python3-dev python3-pip build-essential \
    python3-jinja2 python3-pygments ghostscript doxygen python3-yaml python3-pip clang-format git
RUN cd /tmp && \
    wget https://github.com/Kitware/CMake/releases/download/v3.20.2/cmake-3.20.2.tar.gz && \
    tar -xzvf cmake-3.20.2.tar.gz && \
    cd cmake-3.20.2/ && \
    ./bootstrap && \
    make && \
    make install
RUN cd /tmp && \
    git clone https://github.com/cheshirekow/cmake_format && \
    cd cmake_format && \
    pip3 install . && \
    pip3 install pytest
RUN wget https://github.com/buildsi/Smeagle/archive/refs/tags/${LIBRARY_VERSION}.tar.gz && \
    tar -xzvf ${LIBRARY_VERSION}.tar.gz && \
    cd Smeagle-${LIBRARY_VERSION} && \
    make
ENV PATH=/Smeagle-${LIBRARY_VERSION}/build/standalone:$PATH
