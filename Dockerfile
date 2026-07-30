FROM python:3.12-slim

# Install system dependencies & Node.js
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install Vite frontend dependencies
RUN cd project/automated_ai/frontend && npm install

# Ensure start.sh has execution permissions
RUN chmod +x start.sh

EXPOSE 5000

CMD ["./start.sh"]