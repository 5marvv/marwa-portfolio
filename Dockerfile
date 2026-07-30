FROM python:3.10-slim

# Install Node.js & PM2
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pm2

WORKDIR /app

# Copy repo content
COPY . .

# Install Python requirements (or virtualenv requirements)
RUN pip install --no-cache-dir -r requirements.txt

# Expose your main gateway port
EXPOSE 5000

# Start all services via PM2 in foreground mode
CMD ["pm2-runtime", "start", "ecosystem.config.js"]