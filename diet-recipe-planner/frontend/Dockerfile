FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json* ./

# Expose Vite dev server port
EXPOSE 5173

# Default command (overridden in docker-compose)
CMD ["sh", "-c", "npm install && npm run dev -- --host 0.0.0.0"]
