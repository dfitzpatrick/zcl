# Pull base image
FROM python:3.6-slim

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
RUN pip install pipenv

COPY Pipfile Pipfile.lock /code/
RUN pipenv install --system
#RUN pipenv install mpyq
#RUN pipenv install s2protocol

# Copy project
COPY . /code/