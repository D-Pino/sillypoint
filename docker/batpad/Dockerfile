# What base image should I use
FROM python:3.12 

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY start.sh /
RUN chmod +x /start.sh

EXPOSE 8000
