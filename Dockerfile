# Pull base image
FROM python:3.6.9-alpine

# Set environment varibles
#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED 1


# Set work directory
WORKDIR /code
COPY . /code/
# for psycopg2
RUN apk update && apk add --no-cache --virtual .build-deps \
    postgresql-dev gcc python3-dev musl-dev libffi-dev && \
    pip install --upgrade pip && pip install pipenv && pipenv install --system \
    && find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + \
    && runDeps="$( \
        scanelf --needed --nobanner --recursive /usr/local \
                | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                | sort -u \
                | xargs -r apk info --installed \
                | sort -u \
    )" \
    && apk add --virtual .rundeps $runDeps \
    && apk del .build-deps

# Install dependenciesdocker
#RUN pip install --upgrade pip
#RUN pip install pipenv

#COPY Pipfile Pipfile.lock /code/
#RUN pipenv install --system

# Copy project
#COPY . /code/