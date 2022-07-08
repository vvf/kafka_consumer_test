FROM python:3.9.5-slim as base
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV PYTHONPATH=/app

WORKDIR /app

EXPOSE 8086

RUN apt-get update \
    && apt-get -y install build-essential libpq-dev libxml2-dev libxslt-dev zlib1g-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists

COPY ./listener /app/

RUN pip install --upgrade pip && \
    pip install wheel ipython && \
    pip install -r /app/requirements.txt

CMD ["python", "-m", "runner"]

FROM base as prod

FROM base as dev
RUN pip install asynctest==0.13.0 \
    pytest==6.2.4 \
    pytest-asyncio==0.15.1 \
    pytest-forked==1.3.0 \
    pytest-metadata==1.11.0 \
    pytest-socket==0.4.0 \
    pytest-cov==3.0.0 \
    pytest-sugar==0.9.4 \
    pytest-xdist==2.2.1 \
    pytest-lazy-fixture==0.6.3 \
    pytest-mock==3.6.1 \
    pytest_order==1.0.1 \
    mock==4.0.3

FROM base as test
RUN apt-get update &&\
    apt-get install -y librdkafka-dev build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install asynctest==0.13.0 \
    crashtest==0.3.1 \
    pytest==6.2.4 \
    pytest-asyncio==0.15.1 \
    pytest-forked==1.3.0 \
    pytest-html==3.1.1 \
    pytest-metadata==1.11.0 \
    pytest-socket==0.4.0 \
    pytest-cov==3.0.0 \
    pytest-sugar==0.9.4 \
    pytest-xdist==2.2.1 \
    pytest-lazy-fixture==0.6.3 \
    pytest-mock==3.6.1 \
    pytest_order==1.0.1 \
    mock==4.0.3
CMD ["py.test", "-n4"]
