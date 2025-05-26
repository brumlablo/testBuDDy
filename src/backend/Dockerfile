FROM python:3.6
EXPOSE 5000
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN apt-get update
RUN pip3 install --upgrade pip
RUN apt-get install -y python-mysqldb
RUN pip3 install --no-cache-dir -r requirements.txt
COPY wait-for-it.sh /wait-for-it.sh
COPY . /app