FROM python:3-slim
ENV PYTHONUNBUFFERED 1
# Dependencies for alpine-based images 
# mariadb-dev - see https://bugs.alpinelinux.org/issues/4768 for libmysqlclient-dev
# postgresql-dev - see https://bugs.alpinelinux.org/issues/3642 for libpq-devs
# RUN apk add --update \
#     mariadb-dev \
#     libffi-dev \
#     gcc \
#     jpeg-dev \
#     linux-headers \
#     musl-dev
RUN apt-get update && apt-get install -y\
    libmysqlclient-dev \
    gcc
RUN mkdir /code /code/production
WORKDIR /code
COPY requirements/*.txt /code/requirements/
RUN pip install --no-cache-dir pip wheel -U
RUN pip install --no-cache-dir -r requirements/local.txt 'django<2.0' && pip install --no-cache-dir -r requirements/test.txt 'django<2.0'
ENTRYPOINT ["bash", "docker-entrypoint.sh"]
COPY . /code/
