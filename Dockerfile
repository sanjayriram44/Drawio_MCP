FROM python:3.10-slim

WORKDIR /app

# Copy your code and env
COPY . /app
COPY .env /app/.env

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose your server port
EXPOSE 8000

# Run your app
CMD ["python", "server.py"]
