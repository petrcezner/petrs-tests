ARG BASE_IMAGE=python:3.9
FROM ${BASE_IMAGE} as base

RUN apt-get install gcc -y
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./test_download.py /app/test_download.py
ENTRYPOINT [ "python" ]
CMD [ "./test_download.py"]
