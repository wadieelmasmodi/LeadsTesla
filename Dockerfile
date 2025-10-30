FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create data directory
RUN mkdir -p /data && chmod 777 /data

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web.py
ENV DATABASE_URL=sqlite:////data/app.db

# Expose web port
EXPOSE 8000

# Copy and set permissions for entrypoint
COPY app/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run the entrypoint script
CMD ["/entrypoint.sh"]