FROM python:3.10-slim

# Install PostgreSQL dependencies
# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc libc-dev libffi-dev supervisor && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a folder for the app
WORKDIR /jobNest

# Copy the requirements.txt file into the workdir
COPY requirements.txt ./

# Install the dependencies
RUN pip3 install -r requirements.txt

# Install watchdog
RUN pip3 install watchdog

# Copy the Django project into the image
COPY . /jobNest
