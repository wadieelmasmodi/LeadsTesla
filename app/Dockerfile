FROM python:3.10-slim
WORKDIR /app

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data and static directories with proper permissions
RUN mkdir -p /data /app/static && chmod 755 /data /app/static

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

# Create a startup script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Start using the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]