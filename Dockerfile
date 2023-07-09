FROM python:3.10

RUN mkdir -p /home/app
COPY . /home/app


RUN pip install -r /home/app/requirements.txt

WORKDIR /home/app
