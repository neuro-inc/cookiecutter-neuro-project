FROM neuromation/base:v1.7.6

ENV DEBIAN_FRONTEND noninteractive
RUN mkdir /project
WORKDIR /project

COPY requirements/apt.txt .
RUN apt-get -qq update && \
    apt-get -qq install --no-install-recommends $(cat apt.txt) && \
    apt-get -qq clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/* && \
    rm apt.txt

COPY setup.cfg .

COPY requirements/python.txt .
RUN pip install --progress-bar=off -U --no-cache-dir -q -r python.txt && \
    rm python.txt

RUN ssh-keygen -f /id_rsa -t rsa -N neuromation -q
