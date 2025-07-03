# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
COPY .env /app/.env

# Install dependencies (including headless Draw.io)
RUN pip install --no-cache-dir -r requirements.txt

# Install Docker CLI in the container to run Docker commands (for headless Draw.io)
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Expose the port that the app will run on (3000 or 8000 based on your configuration)
EXPOSE 8000  

# Run server.py when the container launches
CMD ["python", "server.py"]
