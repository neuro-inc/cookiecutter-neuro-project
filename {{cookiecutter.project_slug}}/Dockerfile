FROM neuromation/base:v1.7.6

RUN mkdir /project
WORKDIR /project

COPY apt.txt .
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get -qq update && \
    cat apt.txt | tr -d "\r" | xargs -I % apt-get -qq install --no-install-recommends % && \
    apt-get -qq clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

COPY setup.cfg .

COPY requirements.txt .
RUN pip install --progress-bar=off -U --no-cache-dir -r requirements.txt

RUN ssh-keygen -f /id_rsa -t rsa -N neuromation -q
