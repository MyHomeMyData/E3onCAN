FROM python:alpine3.19

RUN apk update && apk add --no-cache git

RUN mkdir -p /data
WORKDIR /data
RUN git clone https://github.com/MyHomeMyData/E3onCAN.git

WORKDIR /data/E3onCAN

RUN pip install -r requirements.txt

ENV CLI_ARGS=""

CMD python3 E3onCANcollect.py ${CLI_ARGS}
