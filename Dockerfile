FROM python
ARG BIND_PORT=8081

WORKDIR /opt
RUN mkdir server && mkdir server/config

COPY *.py server/
COPY requirments.txt server/
COPY test/ server/
COPY config/* server/config/

WORKDIR /opt/server
EXPOSE ${BIND_PORT}
RUN python3 -m pip install -r requirments.txt

ENTRYPOINT [ "python3", "./server.py" ]