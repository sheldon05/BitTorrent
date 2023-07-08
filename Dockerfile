FROM python:3.10

RUN pip install fastapi
RUN pip install fastapi_utils
RUN pip install uvicorn
RUN pip install requests

RUN mkdir -p /home/app
COPY . /home/app
RUN cd /home/app