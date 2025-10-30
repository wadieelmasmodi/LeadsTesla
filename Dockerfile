FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
WORKDIR /app
COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
ENV PYTHONUNBUFFERED=1

# Expose web port
EXPOSE 8000

# Start both the web server and the scraper
CMD ["sh", "-c", "python web.py & python main.py"]