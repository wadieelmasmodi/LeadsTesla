FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory with proper permissions
RUN mkdir -p /data && chown pwuser:pwuser /data && chmod 755 /data

COPY . /app
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////data/app.db

# Expose web port
EXPOSE 8000

# Set the correct user
USER pwuser

# Start both the web server and the scraper
CMD ["sh", "-c", "python web.py & python main.py"]