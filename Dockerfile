FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install packages globally
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Ensure start script has execution permissions
RUN chmod +x start.sh

EXPOSE 5000

# Launch all services via start.sh
CMD ["./start.sh"]