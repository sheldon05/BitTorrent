FROM python:3.10

RUN mkdir -p /home/app
COPY . /home/app

RUN pip install anyio==3.7.0
RUN pip install bencode-python3==1.0.2
RUN pip install bencode.py==4.0.0
RUN pip install bitstring==4.0.2
RUN pip install certifi==2023.5.7
RUN pip install charset-normalizer==3.1.0
RUN pip install click==8.1.3
RUN pip install colorama==0.4.6
RUN pip install DateTime==5.1
RUN pip install exceptiongroup==1.1.1
RUN pip install fastapi==0.99.0
RUN pip install fastapi-utils==0.2.1
RUN pip install greenlet==2.0.2
RUN pip install h11==0.14.0
RUN pip install idna==3.4
RUN pip install pydantic==1.10.10
RUN pip install Pyro4==4.82
RUN pip install pytz==2023.3
RUN pip install requests==2.31.0
RUN pip install serpent==1.41
RUN pip install sniffio==1.3.0
RUN pip install SQLAlchemy==1.4.48
RUN pip install starlette==0.27.0
RUN pip install typing_extensions==4.7.0
RUN pip install urllib3==2.0.3
RUN pip install uvicorn==0.22.0
RUN pip install zope.interface==6.0

WORKDIR /home/app
