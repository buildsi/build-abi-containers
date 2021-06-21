FROM ghcr.io/autamus/dyninst
# docker build -t ghcr.io/buildsi/smeagle:0.0.0 .
ENV DEBIAN_FRONTEND=noninteractive
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
RUN git clone https://github.com/buildsi/Smeagle /code && \
    cd /code && \
    make
ENV PATH=/code/build/standalone:$PATH
