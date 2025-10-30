FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory with proper permissions
RUN mkdir -p /data && chown pwuser:pwuser /data && chmod 755 /data

COPY . /app

# Environment configuration
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////data/app.db
ENV DOMAIN=https://api2.energum.earth
ENV PORT=8000
ENV FLASK_APP=web.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Note: ADMIN_KEY should be set in Coolify environment variables

# Expose web port
EXPOSE 8000

# Set the correct user
USER pwuser

# Create a startup script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Start using the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]