FROM ubuntu:trusty
MAINTAINER Paul Bowsher <paul.bowsher@gmail.com>

RUN apt-get update
RUN apt-get install -y python
RUN apt-get install -y python-pip
RUN apt-get install -y libssl-dev
RUN apt-get install -y python-dev
RUN apt-get install -y libffi-dev

ADD requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

ADD . /app

ENV PORT 8000
EXPOSE 8000

CMD ["python","server.py"]