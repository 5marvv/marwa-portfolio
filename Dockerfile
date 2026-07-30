FROM python:3.12-slim

# Install system dependencies & Node.js 20.x
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Install frontend dependencies (with legacy peer deps) and build static dist/ folder
RUN cd project/automated_ai/frontend && npm install --legacy-peer-deps && npm run build

# Grant execute permissions to start script
RUN chmod +x start.sh

EXPOSE 5000

CMD ["./start.sh"]