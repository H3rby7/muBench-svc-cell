FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get -y install vim iproute2 curl
RUN rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install gunicorn

EXPOSE 8080
EXPOSE 51313

COPY src/CellController-mp.py \
     src/ExternalServiceExecutor.py \
     src/InternalServiceExecutor.py \
     src/mub.proto src/mub_pb2.py \
     src/mub_pb2_grpc.py \
     src/gunicorn.conf.py \
     entrypoint.sh \
     ./

CMD [ "/bin/bash", "/app/entrypoint.sh"]

