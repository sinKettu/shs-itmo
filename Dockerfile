FROM python
ARG BIND_PORT=8081

RUN apt update \
    && apt install -y --no-install-recommends vim \
    && apt clean

WORKDIR /opt
RUN mkdir server

COPY *.py server/
COPY requirments.txt server/
COPY static server/static
COPY config server/config

WORKDIR /opt/server
EXPOSE ${BIND_PORT}
RUN python3 -m pip install -r requirments.txt

ENTRYPOINT [ "python3", "./server.py" ]
