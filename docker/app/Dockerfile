FROM python:3.10.14-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install necessary packages
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
    build-essential \
    netcat-traditional \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Add entrypoint file
COPY ./docker/init_app.sh /
RUN chmod +x /init_app.sh

ENTRYPOINT ["/init_app.sh"]